from enum import Enum
from random import random

class Register(Enum):
    R0 = 0,
    R1 = 1, 
    R2 = 2, 
    R3 = 3,
    R4 = 4,
    R5 = 5,
    R6 = 6,
    R7 = 7,
    R8 = 8,
    R9 = 9,
    R10 = 10,
    R11 = 11,
    R12 = 12,
    R13 = 13,
    R14 = 14,
    R15 = 15,
    


class TestCase:
    def __init__(self, encoding):
        self.encoding = encoding

def gen_addis():
    gpr = randint(0, 31)
    imm = randint(0, 65535)

    return f"addis r{gpr}, {imm}"

def main():
    with open("testcases.s", 'w') as testcases:
        testcases.write(gen_addis())

if __name__ == "__main__":
    main()