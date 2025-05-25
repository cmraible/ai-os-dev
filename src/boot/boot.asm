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


cmd_cpu:
    ; Simple CPU info - just vendor
    mov si, msg_cpu_start
    call print_string
    
    ; Get vendor string
    xor eax, eax
    cpuid
    
    ; Print vendor (in EBX,EDX,ECX)
    mov si, msg_cpu_vendor  
    call print_string
    
    ; Print EBX (4 chars)
    mov eax, ebx
    call print_4chars
    ; Print EDX (4 chars)
    mov eax, edx
    call print_4chars
    ; Print ECX (4 chars)
    mov eax, ecx
    call print_4chars
    
    mov al, 0x0D
    call send_char
    mov al, 0x0A
    call send_char
    jmp command_loop

cmd_test:
    ; Simple test
    mov si, msg_test_start
    call print_string
    
    ; Test stack
    mov ax, 0x1234
    push ax
    pop bx
    cmp ax, bx
    jne .fail
    
    ; All pass
    mov si, msg_test_pass
    call print_string
    jmp command_loop
.fail:
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

; Print 4 characters from EAX
print_4chars:
    push ax
    call send_char      ; Print AL
    shr eax, 8
    call send_char      ; Print next byte
    shr eax, 8
    call send_char      ; Print next byte
    shr eax, 8
    call send_char      ; Print last byte
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
msg_boot:       db 'AI-OS v0.3', 0x0D, 0x0A, 0
msg_pong:       db 'PONG', 0x0D, 0x0A, 0
msg_info:       db 'v0.3', 0x0D, 0x0A, 0
msg_help:       db 'p=ping c=cpu t=test r=reboot', 0x0D, 0x0A, 0
msg_error:      db 'ERR', 0x0D, 0x0A, 0
msg_test_start: db 'Test...', 0x0D, 0x0A, 0
msg_test_pass:  db 'OK', 0x0D, 0x0A, 0
msg_test_fail:  db 'FAIL', 0x0D, 0x0A, 0
msg_reboot:     db 'Boot', 0x0D, 0x0A, 0

; CPU info messages
msg_cpu_start:  db 'CPU:', 0
msg_cpu_vendor: db ' ', 0

; Pad to 510 bytes and add boot signature
times 510-($-$$) db 0
dw BOOT_SIGNATURE