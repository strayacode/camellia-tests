from enum import Enum
from random import random

def gen_addis():
    gpr = randint(0, 31)
    imm = randint(0, 65535)

    return f"addis r{gpr}, {imm}"

def main():
    with open("testcases.s", 'w') as testcases:
        testcases.write(gen_addis())

if __name__ == "__main__":
    main()