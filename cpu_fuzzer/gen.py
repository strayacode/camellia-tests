import os
import random
import subprocess
import sys

TESTCASES_SOURCE_PATH   = "testcases.s"
FUZZER_BIN_PATH         = "cpu_fuzzer.bin"
FUZZER_DOL_PATH         = "cpu_fuzzer.dol"
DOLPHIN_PATH            = "dolphin-emu-nogui"
VASM_PATH               = "vasmppc_std"
DOLPHIN_LOG             = "dolphin.log"
LITERAL_POOL_BASE_ADDR  = 0x80080000
LITERAL_POOL_SIZE       = 0x10000

def sext(value, bits):
    mask = 2**(bits - 1)
    return -(value & mask) + (value & ~mask)

def simm():
    return hex(sext(random.randint(0, 0xffff), 16))

def uimm():
    return hex(random.randint(0, 0xffff))

def gpr():
    return f"r{random.randint(0, 31)}"

def fpr():
    return f"f{random.randint(0, 31)}"

def oe():
    return random.choice(["", "o"])

def rc():
    return random.choice(["", "."])

def crfd():
    return random.randint(0, 7)

def l():
    return random.randint(0, 1)

def me():
    return random.randint(0, 31)

def mb():
    return random.randint(0, 31)

def sh():
    return random.randint(0, 31)

def to():
    return random.randint(0, 31)

def emit_random_state(file):
    for i in range(0, 32):
        value = random.randint(0, 0xffffffff)
        file.write(f"lis r{i}, {hex(value >> 16)}\n")
        file.write(f"addi r{i}, r{i}, {hex(sext(value & 0xffff, 16))}\n")

def random_literal_pool_access(file, size):
    ra = gpr()
    if ra == 0:
        ra = 31
    
    file.write(f"lis {ra}, {hex(LITERAL_POOL_BASE_ADDR >> 16)}\n")
    file.write(f"addi {ra}, {ra}, {hex(sext(LITERAL_POOL_BASE_ADDR & 0xffff, 16))}\n")
    
    offset = random.randint(LITERAL_POOL_SIZE / size) * size
    return ra, offset

def int_to_bytes(int):
    return [
        (int >> 24) & 0xff,
        (int >> 16) & 0xff,
        (int >>  8) & 0xff,
        (int >>  0) & 0xff
    ]

# integer instructions
def emit_addcx(file):
    file.write(f"addc{oe()}{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_addex(file):
    file.write(f"adde{oe()}{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_addi(file):
    file.write(f"addi {gpr()}, {gpr()}, {simm()}\n")

def emit_addic(file):
    file.write(f"addic {gpr()}, {gpr()}, {simm()}\n")

def emit_addic_rc(file):
    file.write(f"addic. {gpr()}, {gpr()}, {simm()}\n")

def emit_addis(file):
    file.write(f"addis {gpr()}, {gpr()}, {simm()}\n")

def emit_addmex(file):
    file.write(f"addme{oe()}{rc()} {gpr()}, {gpr()}\n")

def emit_addzex(file):
    file.write(f"addze{oe()}{rc()} {gpr()}, {gpr()}\n")

def emit_addx(file):
    file.write(f"add{oe()}{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_andcx(file):
    file.write(f"andc{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_andi_rc(file):
    file.write(f"andi. {gpr()}, {gpr()}, {uimm()}\n")

def emit_andis_rc(file):
    file.write(f"andis. {gpr()}, {gpr()}, {uimm()}\n")

def emit_andx(file):
    file.write(f"and{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_cmp(file):
    file.write(f"cmp {crfd()}, {l()}, {gpr()}, {gpr()}\n")

def emit_cmpi(file):
    file.write(f"cmpi {crfd()}, {l()}, {gpr()}, {simm()}\n")

def emit_cmpl(file):
    file.write(f"cmpl {crfd()}, {l()}, {gpr()}, {gpr()}\n")

def emit_cmpli(file):
    file.write(f"cmpli {crfd()}, {l()}, {gpr()}, {uimm()}\n")

def emit_cntlzwx(file):
    file.write(f"cntlzw{rc()} {gpr()}, {gpr()}\n")

def emit_divwux(file):
    file.write(f"divwu{oe()}{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_divwx(file):
    file.write(f"divw{oe()}{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_eqvx(file):
    file.write(f"eqv{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_extsbx(file):
    file.write(f"extsb{rc()} {gpr()}, {gpr()}\n")

def emit_extshx(file):
    file.write(f"extsh{rc()} {gpr()}, {gpr()}\n")

def emit_mulhwux(file):
    file.write(f"mulhwu{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_mulhwx(file):
    file.write(f"mulhw{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_mulli(file):
    file.write(f"mulli {gpr()}, {gpr()}, {simm()}\n")

def emit_mullwx(file):
    file.write(f"mullw{oe()}{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_nandx(file):
    file.write(f"nand{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_negx(file):
    file.write(f"neg{oe()}{rc()} {gpr()}, {gpr()}\n")

def emit_norx(file):
    file.write(f"nor{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_orcx(file):
    file.write(f"orc{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_ori(file):
    file.write(f"ori {gpr()}, {gpr()}, {uimm()}\n")

def emit_oris(file):
    file.write(f"oris {gpr()}, {gpr()}, {uimm()}\n")

def emit_orx(file):
    file.write(f"or{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_rlwimix(file):
    file.write(f"rlwimi{rc()} {gpr()}, {gpr()}, {sh()}, {mb()}, {me()}\n")

def emit_rlwinmx(file):
    file.write(f"rlwinm{rc()} {gpr()}, {gpr()}, {sh()}, {mb()}, {me()}\n")

def emit_rlwnmx(file):
    file.write(f"rlwnm{rc()} {gpr()}, {gpr()}, {sh()}, {mb()}, {me()}\n")

def emit_slwx(file):
    file.write(f"slw{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_srawix(file):
    file.write(f"srawi{rc()} {gpr()}, {gpr()}, {sh()}\n")

def emit_srawx(file):
    file.write(f"sraw{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_srwx(file):
    file.write(f"srw{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_subfcx(file):
    file.write(f"subfc{oe()}{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_subfex(file):
    file.write(f"subfe{oe()}{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_subfic(file):
    file.write(f"subfic {gpr()}, {gpr()}, {simm()}\n")

def emit_subfmex(file):
    file.write(f"subfme{oe()}{rc()} {gpr()}, {gpr()}\n")

def emit_subfzex(file):
    file.write(f"subfze{oe()}{rc()} {gpr()}, {gpr()}\n")

def emit_subfx(file):
    file.write(f"subf{oe()}{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_tw(file):
    file.write(f"tw {to()}, {gpr()}, {gpr()}\n")

def emit_twi(file):
    file.write(f"twi {to()}, {gpr()}, {simm()}\n")

def emit_xori(file):
    file.write(f"xori {gpr()}, {gpr()}, {uimm()}\n")

def emit_xoris(file):
    file.write(f"xoris {gpr()}, {gpr()}, {uimm()}\n")

def emit_xorx(file):
    file.write(f"xor{rc()} {gpr()}, {gpr()}, {gpr()}\n")

def emit_fabsx(file):
    file.write(f"fabs{rc()} {fpr()}, {fpr()}\n")

def emit_faddsx(file):
    file.write(f"fadds{rc()} {fpr()}, {fpr()}, {fpr()}\n")

def emit_faddx(file):
    file.write(f"fadd{rc()} {fpr()}, {fpr()}, {fpr()}\n")

def emit_fcmpo(file):
    file.write(f"fcmpo {crfd()}, {fpr()}, {fpr()}\n")

def emit_fcmpu(file):
    file.write(f"fcmpu {crfd()}, {fpr()}, {fpr()}\n")

def emit_fctiwzx(file):
    file.write(f"fctiwz{rc()} {fpr()}, {fpr()}\n")

def emit_fctiwx(file):
    file.write(f"fctiw{rc()} {fpr()}, {fpr()}\n")

def emit_fdivsx(file):
    file.write(f"fdivs{rc()} {fpr()}, {fpr()}, {fpr()}\n")

def emit_fdivx(file):
    file.write(f"fdiv{rc()} {fpr()}, {fpr()}, {fpr()}\n")

def emit_fmaddsx(file):
    file.write(f"fmadds{rc()} {fpr()}, {fpr()}, {fpr()}, {fpr()}\n")

def emit_fmaddx(file):
    file.write(f"fmadd{rc()} {fpr()}, {fpr()}, {fpr()}, {fpr()}\n")

def emit_fmrx(file):
    file.write(f"fmr{rc()} {fpr()}, {fpr()}\n")

def emit_fmsubsx(file):
    file.write(f"fmsubs{rc()} {fpr()}, {fpr()}, {fpr()}, {fpr()}\n")

def emit_fmsubx(file):
    file.write(f"fmsub{rc()} {fpr()}, {fpr()}, {fpr()}, {fpr()}\n")

def emit_fmulsx(file):
    file.write(f"fmuls{rc()} {fpr()}, {fpr()}, {fpr()}\n")

def emit_fmulx(file):
    file.write(f"fmul{rc()} {fpr()}, {fpr()}, {fpr()}\n")

def emit_fnabsx(file):
    file.write(f"fnabs{rc()} {fpr()}, {fpr()}\n")

def emit_fnegx(file):
    file.write(f"fneg{rc()} {fpr()}, {fpr()}\n")

def emit_fnmaddsx(file):
    file.write(f"fnmadds{rc()} {fpr()}, {fpr()}, {fpr()}, {fpr()}\n")

def emit_fnmaddx(file):
    file.write(f"fnmadd{rc()} {fpr()}, {fpr()}, {fpr()}, {fpr()}\n")

def emit_fnmsubsx(file):
    file.write(f"fnmsubs{rc()} {fpr()}, {fpr()}, {fpr()}, {fpr()}\n")

def emit_fnmsubx(file):
    file.write(f"fnmsub{rc()} {fpr()}, {fpr()}, {fpr()}, {fpr()}\n")

def emit_fresx(file):
    file.write(f"fres{rc()} {fpr()}, {fpr()}\n")

def emit_frspx(file):
    file.write(f"frsp{rc()} {fpr()}, {fpr()}\n")

def emit_frsqrtex(file):
    file.write(f"frsqrte{rc()} {fpr()}, {fpr()}\n")

def emit_fselx(file):
    file.write(f"fsel{rc()} {fpr()}, {fpr()}, {fpr()}, {fpr()}\n")

def emit_fsubsx(file):
    file.write(f"fsubs{rc()} {fpr()}, {fpr()}, {fpr()}\n")

def emit_lfd(file):
    ra, imm = random_literal_pool_access(file, 8)
    file.write(f"lfd {fpr()}, {imm}({ra})\n")

def emit_lfs(file):
    ra, imm = random_literal_pool_access(file, 8)
    file.write(f"lfs {fpr()}, {imm}({ra})\n")

integer_emitters = [
    emit_addcx,
    emit_addex,
    emit_addi,
    emit_addic,
    emit_addic_rc,
    emit_addis,
    emit_addmex,
    emit_addzex,
    emit_addx,
    emit_andcx,
    emit_andi_rc,
    emit_andis_rc,
    emit_andx,
    emit_cmp,
    emit_cmpi,
    emit_cmpl,
    emit_cmpli,
    emit_cntlzwx,
    emit_divwux,
    emit_divwx,
    emit_eqvx,
    emit_extsbx,
    emit_extshx,
    emit_mulhwux,
    emit_mulhwx,
    emit_mulli,
    emit_mullwx,
    emit_nandx,
    emit_negx,
    emit_norx,
    emit_orcx,
    emit_ori,
    emit_oris,
    emit_orx,
    emit_rlwimix,
    emit_rlwinmx,
    emit_rlwnmx,
    emit_slwx,
    emit_srawix,
    emit_srawx,
    emit_srwx,
    emit_subfcx,
    emit_subfex,
    emit_subfic,
    emit_subfmex,
    emit_subfzex,
    emit_subfx,
    # emit_tw,
    # emit_twi,
    emit_xori,
    emit_xoris,
    emit_xorx,
]

floating_point_emitters = [
    emit_fabsx,
    emit_faddsx,
    emit_faddx,
    emit_faddsx,
    emit_fcmpo,
    emit_fcmpu,
    emit_fctiwzx,
    emit_fctiwx,
    emit_fdivsx,
    emit_fdivx,
    emit_fmaddsx,
    emit_fmaddx,
    emit_fmrx,
    emit_fmsubsx,
    emit_fmsubx,
    emit_fmulsx,
    emit_fmulx,
    emit_fnabsx,
    emit_fnegx,
    emit_fnmaddsx,
    emit_fnmaddx,
    emit_fnmsubsx,
    emit_fnmsubx,
    emit_fresx,
    emit_frspx,
    emit_frsqrtex,
    emit_fselx,
    emit_fsubsx
]

def emit_integer_tests(file):
    for i in range(10000):
        random.choice(integer_emitters)(file)

    for i in range(10000):
        random.choice(floating_point_emitters)(file)

# floating point instructions
# paired single instructions
# load and store instructions
# branch instructions
# system instructions

def emit_tests():
    with open(TESTCASES_SOURCE_PATH, 'w') as testcases:
        testcases.write("_start:\n")
        emit_random_state(testcases)

        emit_integer_tests(testcases)

        testcases.write("end:\n")
        testcases.write("   b end\n")

def compile_tests():
    # call this command
    # ./vasmppc_std -Fbin -big -o fuzzer.dol source/main.s
    
    subprocess.run([
        VASM_PATH,
        "-Fbin",
        "-big",
        "-o", FUZZER_BIN_PATH,
        TESTCASES_SOURCE_PATH
    ])

    binary_size_raw = os.stat(FUZZER_BIN_PATH).st_size

    binary_size   = int_to_bytes(binary_size_raw)
    binary_ofs    = int_to_bytes(0x100)
    binary_addr   = int_to_bytes(0x80004000)
    lit_pool_size = int_to_bytes(LITERAL_POOL_SIZE)
    lit_pool_ofs  = int_to_bytes(0x100 + binary_size_raw)
    lit_pool_addr = int_to_bytes(LITERAL_POOL_BASE_ADDR)

    lit_pool = [random.randint(0, 255) for i in range(LITERAL_POOL_SIZE)]

    with open(FUZZER_DOL_PATH, 'wb') as dol:
        # insert the dol header
        dol.write(bytearray([
            ] + binary_ofs + [      0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, ] + lit_pool_ofs + [
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, ] + binary_addr + [     0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, ] + lit_pool_addr + [   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            ] + binary_size +      [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, ] + lit_pool_size + [
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x80, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ]))

        with open(FUZZER_BIN_PATH, 'rb') as bin:
            dol.write(bin.read())
            dol.write(bytearray(lit_pool))

def run_tests():
    dolphin_log = open(DOLPHIN_LOG, "w")
    p = subprocess.run([
        DOLPHIN_PATH, 
        "-e", FUZZER_DOL_PATH, 
        "--platform=headless"
    ], stdout=dolphin_log)

def main():
    emit_tests()

    if "--emit" in sys.argv[1:]:
        return

    compile_tests()

    if "--compile" in sys.argv[1:]:
        return

    run_tests()

if __name__ == "__main__":
    main()