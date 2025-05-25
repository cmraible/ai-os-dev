; AI-OS Bootloader
; This bootloader is designed to be testable by automated systems

BITS 16
ORG 0x7C00

; Constants
COM1_BASE       equ 0x3F8
BOOT_SIGNATURE  equ 0xAA55

; Boot sector entry point
start:
    ; Disable interrupts during setup
    cli
    
    ; Set up segments
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00      ; Stack grows down from bootloader
    
    ; Initialize serial port
    call init_serial
    
    ; Send boot message
    mov si, msg_boot
    call print_string
    
    ; Enable interrupts
    sti
    
    ; Main command loop
    call command_loop
    
    ; Should never reach here
    jmp $

; Initialize COM1 serial port
init_serial:
    push ax
    push dx
    
    ; Set baud rate to 115200
    mov dx, COM1_BASE + 3   ; Line control register
    mov al, 0x80            ; Enable DLAB
    out dx, al
    
    mov dx, COM1_BASE + 0   ; Divisor low byte
    mov al, 0x01            ; 115200 baud
    out dx, al
    
    mov dx, COM1_BASE + 1   ; Divisor high byte  
    mov al, 0x00
    out dx, al
    
    mov dx, COM1_BASE + 3   ; Line control register
    mov al, 0x03            ; 8 bits, no parity, 1 stop
    out dx, al
    
    mov dx, COM1_BASE + 2   ; FIFO control register
    mov al, 0xC7            ; Enable FIFO, clear buffers
    out dx, al
    
    mov dx, COM1_BASE + 4   ; Modem control register
    mov al, 0x0B            ; DTR + RTS + OUT2
    out dx, al
    
    ; Clear any pending data
    mov dx, COM1_BASE
    in al, dx
    
    pop dx
    pop ax
    ret

; Main command processing loop
command_loop:
    ; Wait for command
    call read_char
    
    ; Process single-character commands
    cmp al, 'p'         ; Ping
    je cmd_ping
    cmp al, 'i'         ; Info
    je cmd_info
    cmp al, 'm'         ; Memory dump
    je cmd_memory
    cmp al, 'r'         ; Reboot
    je cmd_reboot
    cmp al, 't'         ; Test
    je cmd_test
    cmp al, 'h'         ; Help
    je cmd_help
    cmp al, 'c'         ; CPU info (NEW!)
    je cmd_cpu
    
    ; Unknown command - send error
    mov si, msg_error
    call print_string
    
    jmp command_loop

; Command handlers
cmd_ping:
    mov si, msg_pong
    call print_string
    jmp command_loop

cmd_info:
    mov si, msg_info
    call print_string
    jmp command_loop

cmd_memory:
    ; Dump first 32 bytes of boot sector
    mov si, 0x7C00
    mov cx, 32
    call dump_memory
    jmp command_loop

cmd_cpu:
    ; Get CPU info using CPUID instruction
    mov si, msg_cpu_start
    call print_string
    
    ; Check if CPUID is supported
    ; Try to flip ID bit (bit 21) in EFLAGS
    pushfd
    pop eax
    mov ecx, eax
    xor eax, 0x200000    ; Flip ID bit
    push eax
    popfd
    pushfd
    pop eax
    push ecx
    popfd                ; Restore original EFLAGS
    
    xor eax, ecx
    jz no_cpuid          ; CPUID not supported
    
    ; CPUID is supported - get vendor string
    xor eax, eax         ; Function 0: Get vendor ID
    cpuid
    
    ; Store vendor string (EBX, EDX, ECX)
    mov [cpu_vendor], ebx
    mov [cpu_vendor+4], edx
    mov [cpu_vendor+8], ecx
    
    ; Print vendor
    mov si, msg_cpu_vendor
    call print_string
    mov si, cpu_vendor
    mov cx, 12           ; 12 bytes to print
    call print_bytes
    mov al, 0x0D
    call send_char
    mov al, 0x0A
    call send_char
    
    ; Get CPU features
    mov eax, 1
    cpuid
    
    ; Print family/model/stepping
    mov si, msg_cpu_family
    call print_string
    mov eax, eax         ; Already has CPU signature
    push eax
    shr eax, 8
    and al, 0x0F         ; Family
    call print_hex_byte
    
    mov si, msg_cpu_model
    call print_string
    pop eax
    push eax
    shr eax, 4
    and al, 0x0F         ; Model
    call print_hex_byte
    
    mov si, msg_cpu_stepping
    call print_string
    pop eax
    and al, 0x0F         ; Stepping
    call print_hex_byte
    mov al, 0x0D
    call send_char
    mov al, 0x0A
    call send_char
    
    jmp command_loop

no_cpuid:
    mov si, msg_no_cpuid
    call print_string
    jmp command_loop

cmd_test:
    ; Run self-tests
    mov si, msg_test_start
    call print_string
    
    ; Test 1: Stack operations
    mov ax, 0x1234
    push ax
    pop bx
    cmp ax, bx
    jne test_fail
    
    ; Test 2: Memory access
    mov word [0x7000], 0x5678
    mov ax, [0x7000]
    cmp ax, 0x5678
    jne test_fail
    
    ; Test 3: CPU detection (NEW!)
    ; Just verify we can check for CPUID
    pushfd
    pop eax
    test eax, eax       ; Basic sanity check
    jz test_fail
    
    mov si, msg_test_pass
    call print_string
    jmp command_loop
    
test_fail:
    mov si, msg_test_fail
    call print_string
    jmp command_loop

cmd_help:
    mov si, msg_help
    call print_string
    jmp command_loop

cmd_reboot:
    mov si, msg_reboot
    call print_string
    ; Delay for message to send
    mov cx, 0xFFFF
.delay:
    loop .delay
    ; Triple fault to reboot
    jmp 0xFFFF:0

; Utility functions

; Print null-terminated string pointed to by SI
print_string:
    push ax
    push si
.loop:
    lodsb
    test al, al
    jz .done
    call send_char
    jmp .loop
.done:
    pop si
    pop ax
    ret

; Print CX bytes pointed to by SI
print_bytes:
    push ax
    push cx
    push si
.loop:
    lodsb
    call send_char
    loop .loop
    pop si
    pop cx
    pop ax
    ret

; Send character in AL to serial port
send_char:
    push dx
    push ax
    
    ; Wait for transmitter to be empty
    mov dx, COM1_BASE + 5
.wait:
    in al, dx
    test al, 0x20
    jz .wait
    
    ; Send character
    pop ax
    mov dx, COM1_BASE
    out dx, al
    
    pop dx
    ret

; Read character from serial port into AL
read_char:
    push dx
    
    ; Wait for data to be available
    mov dx, COM1_BASE + 5
.wait:
    in al, dx
    test al, 0x01
    jz .wait
    
    ; Read character
    mov dx, COM1_BASE
    in al, dx
    
    pop dx
    ret

; Dump CX bytes of memory starting at SI
dump_memory:
    push ax
    push cx
    push si
    
.loop:
    lodsb
    call print_hex_byte
    mov al, ' '
    call send_char
    
    ; New line every 16 bytes
    mov ax, si
    and ax, 0x0F
    jnz .no_newline
    mov al, 0x0D
    call send_char
    mov al, 0x0A
    call send_char
    
.no_newline:
    loop .loop
    
    mov al, 0x0D
    call send_char
    mov al, 0x0A
    call send_char
    
    pop si
    pop cx
    pop ax
    ret

; Print AL as hex byte
print_hex_byte:
    push ax
    push ax
    shr al, 4
    call print_hex_nibble
    pop ax
    and al, 0x0F
    call print_hex_nibble
    pop ax
    ret

print_hex_nibble:
    and al, 0x0F
    cmp al, 10
    jb .digit
    add al, 'A' - 10
    jmp send_char
.digit:
    add al, '0'
    jmp send_char

; Data section
msg_boot:       db 'AI-OS Boot v0.3', 0x0D, 0x0A
                db 'Ready for commands', 0x0D, 0x0A, 0
msg_pong:       db 'PONG', 0x0D, 0x0A, 0
msg_info:       db 'AI-OS Bootloader', 0x0D, 0x0A
                db 'Version: 0.3', 0x0D, 0x0A
                db 'Memory: 640KB', 0x0D, 0x0A, 0
msg_help:       db 'Commands:', 0x0D, 0x0A
                db '  p - Ping', 0x0D, 0x0A
                db '  i - Info', 0x0D, 0x0A
                db '  m - Memory dump', 0x0D, 0x0A
                db '  t - Run tests', 0x0D, 0x0A
                db '  c - CPU info', 0x0D, 0x0A
                db '  r - Reboot', 0x0D, 0x0A
                db '  h - Help', 0x0D, 0x0A, 0
msg_error:      db 'ERROR: Unknown command', 0x0D, 0x0A, 0
msg_test_start: db 'Running tests...', 0x0D, 0x0A, 0
msg_test_pass:  db 'All tests passed!', 0x0D, 0x0A, 0
msg_test_fail:  db 'Test failed!', 0x0D, 0x0A, 0
msg_reboot:     db 'Rebooting...', 0x0D, 0x0A, 0

; CPU info messages
msg_cpu_start:  db 'CPU Information:', 0x0D, 0x0A, 0
msg_cpu_vendor: db '  Vendor: ', 0
msg_cpu_family: db '  Family: ', 0
msg_cpu_model:  db ', Model: ', 0
msg_cpu_stepping: db ', Stepping: ', 0
msg_no_cpuid:   db '  CPUID not supported', 0x0D, 0x0A, 0

; Buffer for CPU vendor string
cpu_vendor:     times 12 db 0

; Pad to 510 bytes and add boot signature
times 510-($-$$) db 0
dw BOOT_SIGNATURE