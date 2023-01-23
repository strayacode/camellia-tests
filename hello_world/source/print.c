#include "print.h"
#include "types.h"

char buffer[SI_BUFFER_LENGTH];

void init_si_buffer() {
  // TODO: how is the buffer allocated?
  u32* si_buffer_address = (u32*)SI_BUFFER;
  *si_buffer_address = (u32)(&buffer) - sizeof(buffer);
}