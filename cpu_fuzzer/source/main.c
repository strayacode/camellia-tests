#define RUN_TESTS_ADDR 0x80100000

void run_tests(void);

int main(void) {
    run_tests();

    while (1);
}
