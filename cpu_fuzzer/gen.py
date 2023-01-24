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

def gen_tests():
    with open(TESTCASES_SOURCE_PATH, 'w') as testcases:
        testcases.write(".global run_tests\n")
        testcases.write("run_tests:\n")
        # Signal to Dolphin that we're beginning the tests and to start logging
        testcases.write("lis 29, 0x1234;\n")
        testcases.write("addi 29, 29, 0x5678;\n")
        testcases.write("mtctr 29;\n")

        # Perform the tests
        testcases.write(gen_addis() + '\n')
        testcases.write("bl store_cpu_state;\n")

        # Signal to Dolphin that we're done with the tests
        testcases.write("lis 29, 0x8765;\n")
        testcases.write("addi 29, 29, 0x4321;\n")
        testcases.write("mtctr 29;\n")

def run_tests():
    if subprocess.run(["make"]).returncode != 0:
        error("make failed")

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
    gen_tests()
    results = run_tests()

    parse_results(results)

if __name__ == "__main__":
    main()