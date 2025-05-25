# Makefile for bootloader

AS = nasm
ASFLAGS = -f bin

# Default target
all: boot.bin test_boot.bin

boot.bin: boot.asm
	$(AS) $(ASFLAGS) $< -o $@
	@echo "Built boot.bin: $$(stat -c%s $@) bytes"
	test $$(stat -c%s $@) -eq 512 || (echo "ERROR: Boot sector must be exactly 512 bytes!" && false)

test_boot.bin: test_boot.asm
	$(AS) $(ASFLAGS) $< -o $@
	@echo "Built test_boot.bin: $$(stat -c%s $@) bytes"

clean:
	rm -f *.bin *.o

.PHONY: all clean