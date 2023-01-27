import os
import random
import subprocess
import sys

TESTCASES_SOURCE_PATH   = "testcases.s"
FUZZER_BIN_PATH         = "./cpu_fuzzer.bin"
FUZZER_DOL_PATH         = "./cpu_fuzzer.dol"
DOLPHIN_PATH            = "dolphin-emu-nogui"
VASM_PATH               = "./vasmppc_std"

def error(msg):
    print("Error: ", msg)
    exit(-1)

def sext(value, bits):
    mask = 2**(bits - 1)
    return -(value & mask) + (value & ~mask)

def simm():
    return hex(sext(random.randint(0, 0xffff), 16))

def uimm():
    return hex(random.randint(0, 0xffff))

def gpr():
    return f"r{random.randint(0, 31)}"

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
    emit_tw,
    emit_twi,
    emit_xori,
    emit_xoris,
    emit_xorx,
]

def emit_integer_tests(file):
    for i in range(10000):
        random.choice(integer_emitters)(file)

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

    binary_size = os.stat(FUZZER_BIN_PATH).st_size
    binary_size_bytes = [
        (binary_size >> 24) & 0xff,
        (binary_size >> 16) & 0xff,
        (binary_size >>  8) & 0xff,
        (binary_size >>  0) & 0xff
    ]

    print(hex(binary_size))

    with open(FUZZER_DOL_PATH, 'wb') as dol:
        # insert the dol header
        dol.write(bytearray([
            0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            ] + binary_size_bytes +[0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x80, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        ]))

        with open(FUZZER_BIN_PATH, 'rb') as bin:
            # dump the contents of bin into dol
            dol.write(bin.read())

def run_tests():
    p = subprocess.run([
        DOLPHIN_PATH, 
        "-e", FUZZER_DOL_PATH, 
        "--platform=headless"
    ], stdout=subprocess.PIPE)
    
    return p.stdout.decode()

def parse_results(results):
    print(results)
    print(":)")

def main():
    emit_tests()

    if "--emit" in sys.argv[1:]:
        return

    compile_tests()

    if "--compile" in sys.argv[1:]:
        return

    results = run_tests()

    parse_results(results)

if __name__ == "__main__":
    main()