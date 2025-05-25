; Minimal bootloader that responds to serial commands
; Assembles to exactly 512 bytes with boot signature

BITS 16
ORG 0x7C00

start:
    ; Clear interrupts and set up segments
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    
    ; Initialize serial port (COM1 - 0x3F8)
    mov dx, 0x3F8 + 3    ; Line control register
    mov al, 0x80         ; Enable DLAB
    out dx, al
    
    mov dx, 0x3F8 + 0    ; Divisor low byte
    mov al, 0x03         ; 38400 baud
    out dx, al
    
    mov dx, 0x3F8 + 1    ; Divisor high byte
    mov al, 0x00
    out dx, al
    
    mov dx, 0x3F8 + 3    ; Line control register
    mov al, 0x03         ; 8 bits, no parity, 1 stop
    out dx, al
    
    mov dx, 0x3F8 + 2    ; FIFO control register
    mov al, 0xC7         ; Enable FIFO
    out dx, al
    
    mov dx, 0x3F8 + 4    ; Modem control register
    mov al, 0x0B         ; DTR + RTS + OUT2
    out dx, al
    
    ; Send boot message
    mov si, boot_msg
    call print_string
    
    ; Enable interrupts
    sti

main_loop:
    ; Check for serial data
    mov dx, 0x3F8 + 5    ; Line status register
    in al, dx
    test al, 0x01        ; Data ready?
    jz main_loop
    
    ; Read character
    mov dx, 0x3F8
    in al, dx
    
    ; Echo it back
    call send_char
    
    ; Process commands
    cmp al, 'p'          ; Ping command
    je cmd_ping
    cmp al, 'r'          ; Read memory command
    je cmd_read
    cmp al, 'i'          ; Info command
    je cmd_info
    
    jmp main_loop

cmd_ping:
    mov si, pong_msg
    call print_string
    jmp main_loop

cmd_info:
    mov si, info_msg
    call print_string
    jmp main_loop

cmd_read:
    ; Simple memory read - read next 16 bytes from 0x7C00
    mov si, 0x7C00
    mov cx, 16
.read_loop:
    lodsb
    call send_hex_byte
    mov al, ' '
    call send_char
    loop .read_loop
    mov al, 0x0A
    call send_char
    jmp main_loop

; Send null-terminated string
print_string:
    push ax
    push dx
.loop:
    lodsb
    test al, al
    jz .done
    call send_char
    jmp .loop
.done:
    pop dx
    pop ax
    ret

; Send character in AL
send_char:
    push dx
    push ax
    mov dx, 0x3F8 + 5
.wait:
    in al, dx
    test al, 0x20        ; Transmitter empty?
    jz .wait
    pop ax
    mov dx, 0x3F8
    out dx, al
    pop dx
    ret

; Send AL as hex byte
send_hex_byte:
    push ax
    push ax
    shr al, 4
    call send_hex_nibble
    pop ax
    and al, 0x0F
    call send_hex_nibble
    pop ax
    ret

send_hex_nibble:
    and al, 0x0F
    cmp al, 10
    jb .digit
    add al, 'A' - 10
    jmp send_char
.digit:
    add al, '0'
    jmp send_char

; Data
boot_msg:   db 'AI-OS Boot v0.1', 0x0D, 0x0A
            db 'Commands: (p)ing, (r)ead, (i)nfo', 0x0D, 0x0A, 0
pong_msg:   db 'PONG!', 0x0D, 0x0A, 0
info_msg:   db 'CPU: 8086 Mode', 0x0D, 0x0A
            db 'MEM: 640KB', 0x0D, 0x0A, 0

; Pad to 510 bytes and add boot signature
times 510-($-$$) db 0
dw 0xAA55