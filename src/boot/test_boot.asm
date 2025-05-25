; Test-specific bootloader for automated testing
; Responds to a sequence of commands and exits

BITS 16
ORG 0x7C00

start:
    cli
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00
    
    ; Quick serial init
    mov dx, 0x3F8 + 3
    mov al, 0x80
    out dx, al
    mov dx, 0x3F8
    mov al, 0x01
    out dx, al
    inc dx
    xor al, al
    out dx, al
    mov dx, 0x3F8 + 3
    mov al, 0x03
    out dx, al
    
    ; Send test marker
    mov si, test_msg
    call puts
    
    ; Simple echo test
.echo:
    call getc
    cmp al, 'q'     ; Quit command
    je .quit
    call putc       ; Echo back
    jmp .echo
    
.quit:
    mov si, quit_msg
    call puts
    hlt

putc:
    push dx
    mov dx, 0x3F8 + 5
.wait:    
    in al, dx
    test al, 0x20
    jz .wait
    mov dx, 0x3F8
    out dx, al
    pop dx
    ret

getc:
    mov dx, 0x3F8 + 5
.wait:
    in al, dx
    test al, 0x01
    jz .wait
    mov dx, 0x3F8
    in al, dx
    ret

puts:
    lodsb
    test al, al
    jz .done
    call putc
    jmp puts
.done:
    ret

test_msg: db 'TEST_BOOT_OK', 0x0D, 0x0A, 0
quit_msg: db 'QUIT_OK', 0x0D, 0x0A, 0

times 510-($-$$) db 0
dw 0xAA55