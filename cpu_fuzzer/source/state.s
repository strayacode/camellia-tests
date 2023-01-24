.global store_cpu_state

store_cpu_state:
    mtspr 9, 0;
    
    lis 1, 0x8600;
    stmw 2, 8(1);
    mfspr 0, 9;
    stw 0, 0(1);
    stw 1, 4(1);

    blr;
