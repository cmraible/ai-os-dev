#!/usr/bin/env python3
"""
QEMU Development Environment for AI OS
This script sets up and manages the QEMU environment for bootloader/OS development
"""

import os
import sys
import subprocess
import json
import time
import threading
import queue
from flask import Flask, request, jsonify
import serial
import struct

app = Flask(__name__)

# Global state
qemu_process = None
serial_port = None
output_queue = queue.Queue()
boot_image_path = "boot.bin"

class QEMUManager:
    def __init__(self):
        self.process = None
        self.serial = None
        self.monitor = None
        
    def compile_bootloader(self, asm_code):
        """Compile assembly code to binary bootloader"""
        # Write assembly code
        with open('boot.asm', 'w') as f:
            f.write(asm_code)
        
        # Compile with NASM
        try:
            subprocess.run(['nasm', '-f', 'bin', 'boot.asm', '-o', 'boot.bin'], 
                         check=True, capture_output=True, text=True)
            return True, "Compilation successful"
        except subprocess.CalledProcessError as e:
            return False, f"Compilation failed: {e.stderr}"
    
    def start_qemu(self):
        """Start QEMU with our bootloader"""
        if self.process:
            self.stop_qemu()
        
        cmd = [
            'qemu-system-x86_64',
            '-drive', f'format=raw,file={boot_image_path}',
            '-m', '128',  # 128MB RAM
            '-serial', 'tcp::5555,server,nowait',  # Serial on TCP port
            '-monitor', 'tcp::5556,server,nowait',  # Monitor on TCP port
            '-display', 'none',  # Headless
            '-no-reboot',  # Don't reboot on triple fault
            '-d', 'int,cpu_reset',  # Debug interrupts and resets
            '-D', 'qemu.log'  # Log to file
        ]
        
        self.process = subprocess.Popen(cmd)
        time.sleep(1)  # Give QEMU time to start
        
        # Connect to serial
        try:
            import socket
            self.serial = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serial.connect(('localhost', 5555))
            self.serial.settimeout(0.1)
        except:
            return False, "Failed to connect to serial port"
        
        return True, "QEMU started successfully"
    
    def stop_qemu(self):
        """Stop QEMU"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        if self.serial:
            self.serial.close()
            self.serial = None
    
    def send_serial(self, data):
        """Send data to serial port"""
        if self.serial:
            if isinstance(data, str):
                data = data.encode()
            self.serial.send(data)
            return True
        return False
    
    def read_serial(self, timeout=0.1):
        """Read from serial port"""
        if not self.serial:
            return b''
        
        try:
            self.serial.settimeout(timeout)
            data = self.serial.recv(4096)
            return data
        except socket.timeout:
            return b''
        except:
            return b''
    
    def read_memory(self, address, size):
        """Read memory via QEMU monitor"""
        # This would connect to monitor port and use 'x' command
        # Simplified for now
        return b'\x00' * size

qemu = QEMUManager()

# Flask API endpoints
@app.route('/compile', methods=['POST'])
def compile():
    """Compile assembly code"""
    code = request.json.get('code', '')
    success, message = qemu.compile_bootloader(code)
    return jsonify({'success': success, 'message': message})

@app.route('/flash', methods=['POST'])
def flash():
    """Flash bootloader and restart QEMU"""
    # If code provided, compile first
    if 'code' in request.json:
        success, message = qemu.compile_bootloader(request.json['code'])
        if not success:
            return jsonify({'success': False, 'message': message})
    
    # Restart QEMU with new image
    success, message = qemu.start_qemu()
    return jsonify({'success': success, 'message': message})

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the system"""
    qemu.stop_qemu()
    success, message = qemu.start_qemu()
    return jsonify({'success': success, 'message': message})

@app.route('/serial', methods=['POST'])
def send_serial():
    """Send data to serial port"""
    data = request.json.get('data', '')
    if isinstance(data, list):
        # Handle byte array
        data = bytes(data)
    success = qemu.send_serial(data)
    return jsonify({'success': success})

@app.route('/serial', methods=['GET'])
def read_serial():
    """Read from serial port"""
    data = qemu.read_serial(timeout=0.5)
    return jsonify({
        'data': list(data),  # Return as byte array
        'text': data.decode('utf-8', errors='replace')
    })

@app.route('/memory/<int:address>/<int:size>', methods=['GET'])
def read_memory(address, size):
    """Read memory at address"""
    data = qemu.read_memory(address, size)
    return jsonify({'data': list(data)})

@app.route('/status', methods=['GET'])
def status():
    """Get system status"""
    return jsonify({
        'running': qemu.process is not None and qemu.process.poll() is None,
        'pid': qemu.process.pid if qemu.process else None
    })

if __name__ == '__main__':
    print("AI OS Development Environment")
    print("Starting Flask API on http://localhost:5000")
    print("\nEndpoints:")
    print("  POST /compile - Compile assembly code")
    print("  POST /flash   - Flash and boot")
    print("  POST /reset   - Reset system")
    print("  POST /serial  - Send serial data")
    print("  GET  /serial  - Read serial data")
    print("  GET  /memory/<addr>/<size> - Read memory")
    print("  GET  /status  - System status")
    
    app.run(host='0.0.0.0', port=5000, debug=False)