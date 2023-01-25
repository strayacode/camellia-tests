from elftools.elf.elffile import ELFFile
import random
import subprocess

TESTCASES_SOURCE_PATH   = "source/testcases.s"
FUZZER_DOL_PATH         = "./cpu_fuzzer.dol"
DOLPHIN_PATH            = "dolphin-emu-nogui"
FUZZER_TMP_RESULTS_PATH = "./camellia_fuzzer.log"

def error(msg):
    print("Error: ", msg)
    exit(-1)

def gen_addis():
    gpr = random.randint(0, 31)
    imm = random.randint(0, 65535)

    return f"addis {gpr}, {gpr}, {imm};"

def emit_random_state(file):
    for i in range(0, 32):
        value = random.randint(0, 0xffffffff)
        file.write(f"lis r{i}, {hex(value >> 16)}\n")
        file.write(f"addi r{i}, {hex(value & 0xffff)}\n")

def emit_tests():
    with open(TESTCASES_SOURCE_PATH, 'w') as testcases:
        testcases.write("_start:\n")
        emit_random_state(testcases)

def run_tests():
    # TODO: figure out the command we need for compiling
    # if subprocess.run(["make"]).returncode != 0:
    #     error("make failed")

    # call this command
    # ./vasmppc_std -Fbin -big -o fuzzer.dol source/main.s

    # pass the addr into dolphin so it knows where to put its PC
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
    results = run_tests()

    parse_results(results)

if __name__ == "__main__":
    main()