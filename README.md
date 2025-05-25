# AI OS Development Environment

A QEMU-based development environment designed for AI-driven operating system development.

## Features

- **HTTP API** for AI interaction with hardware
- **Automated compilation** of assembly code to bootable images
- **Serial communication** for testing and debugging
- **Memory inspection** capabilities
- **Headless operation** optimized for AI development

## Quick Start

1. Install dependencies:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

2. Start the development server:
   ```bash
   python3 setup.py
   ```

3. Test the environment:
   ```bash
   python3 test_client.py
   ```

## API Endpoints

- `POST /compile` - Compile assembly code
- `POST /flash` - Flash bootloader and restart
- `POST /reset` - Reset the system
- `POST /serial` - Send data to serial port
- `GET /serial` - Read from serial port
- `GET /memory/<address>/<size>` - Read memory
- `GET /status` - Get system status

## Example Usage

```python
import requests

# Compile and flash a bootloader
r = requests.post('http://localhost:5000/flash', json={
    'code': open('boot.asm').read()
})

# Send command
r = requests.post('http://localhost:5000/serial', json={
    'data': 'p'  # Send ping command
})

# Read response
r = requests.get('http://localhost:5000/serial')
print(r.json()['text'])
```

## Architecture

- QEMU provides x86_64 emulation
- Serial port for bidirectional communication
- Monitor port for debugging and memory inspection
- Flask API wraps all functionality for easy AI access

## Next Steps

1. Extend the bootloader with more commands
2. Implement protected mode switching
3. Add basic memory management
4. Create a simple kernel
