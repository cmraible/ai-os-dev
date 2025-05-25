"""Pytest configuration for OS tests"""

import pytest
import os
import subprocess
import time
import socket
import threading
import queue
from pathlib import Path

@pytest.fixture(scope="session")
def output_dir():
    """Create output directory for test artifacts"""
    output = Path("output")
    output.mkdir(exist_ok=True)
    return output

@pytest.fixture
def qemu_runner(output_dir):
    """Fixture to run QEMU with a given boot image"""
    class QEMURunner:
        def __init__(self):
            self.process = None
            self.serial = None
            self.output_queue = queue.Queue()
            self.reader_thread = None
            
        def start(self, boot_image, timeout=5):
            """Start QEMU with the given boot image"""
            if self.process:
                self.stop()
            
            # Start QEMU
            cmd = [
                'qemu-system-x86_64',
                '-drive', f'format=raw,file={boot_image}',
                '-m', '128',
                '-serial', 'tcp::5555,server,nowait',
                '-display', 'none',
                '-no-reboot',
                '-d', 'cpu_reset,int',
                '-D', str(output_dir / 'qemu_debug.log')
            ]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give QEMU time to start
            time.sleep(0.5)
            
            # Connect to serial port
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    self.serial = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.serial.connect(('localhost', 5555))
                    self.serial.settimeout(0.1)
                    break
                except:
                    time.sleep(0.1)
            
            if not self.serial:
                raise RuntimeError("Failed to connect to QEMU serial port")
            
            # Start reader thread
            self.reader_thread = threading.Thread(target=self._reader)
            self.reader_thread.daemon = True
            self.reader_thread.start()
            
            return self
        
        def _reader(self):
            """Background thread to read serial output"""
            buffer = b''
            while self.serial:
                try:
                    data = self.serial.recv(1024)
                    if data:
                        buffer += data
                        # Look for complete lines
                        while b'\n' in buffer:
                            line, buffer = buffer.split(b'\n', 1)
                            self.output_queue.put(line.strip())
                except socket.timeout:
                    pass
                except:
                    break
        
        def send(self, data):
            """Send data to serial port"""
            if isinstance(data, str):
                data = data.encode()
            self.serial.send(data)
        
        def read_line(self, timeout=2):
            """Read a line from serial output"""
            try:
                return self.output_queue.get(timeout=timeout)
            except queue.Empty:
                return None
        
        def read_until(self, expected, timeout=5):
            """Read until expected string is found"""
            start_time = time.time()
            lines = []
            while time.time() - start_time < timeout:
                line = self.read_line(timeout=0.1)
                if line:
                    lines.append(line)
                    if expected.encode() in line:
                        return lines
            return lines
        
        def stop(self):
            """Stop QEMU"""
            if self.serial:
                self.serial.close()
                self.serial = None
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
    
    runner = QEMURunner()
    yield runner
    runner.stop()