.global _start

.include "dol.s"

_start:
    lis r0, 0x1234
    addi r0, r0, 0x5678

end:
    b end