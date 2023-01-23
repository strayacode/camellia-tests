#ifndef PRINT_H
#define PRINT_H

#include <stdio.h>

#define SI_BUFFER 0xcc006480
#define SI_BUFFER_LENGTH 0x800

extern char buffer[SI_BUFFER_LENGTH];

void init_si_buffer();

#define print(format, ...) sprintf(buffer, format, ##__VA_ARGS__)

#endif