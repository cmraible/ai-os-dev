"""Tests for the bootloader"""

import pytest
import time
from pathlib import Path

class TestBootloader:
    """Basic bootloader functionality tests"""
    
    def test_boot_message(self, qemu_runner, output_dir):
        """Test that bootloader sends initial message"""
        boot_image = Path("../src/boot/boot.bin")
        assert boot_image.exists(), "Boot image not found - run make first"
        
        # Start QEMU
        qemu_runner.start(boot_image)
        
        # Read boot message
        lines = qemu_runner.read_until("Ready for commands", timeout=2)
        
        # Save output
        with open(output_dir / "serial_boot.txt", "wb") as f:
            for line in lines:
                f.write(line + b"\n")
        
        # Verify boot message
        assert any(b"AI-OS Boot" in line for line in lines), "Boot message not found"
        assert any(b"Ready for commands" in line for line in lines), "Ready message not found"
    
    def test_ping_command(self, qemu_runner, output_dir):
        """Test ping command"""
        boot_image = Path("../src/boot/boot.bin")
        qemu_runner.start(boot_image)
        
        # Wait for boot
        qemu_runner.read_until("Ready for commands", timeout=2)
        
        # Send ping
        qemu_runner.send('p')
        
        # Read response
        response = qemu_runner.read_line(timeout=1)
        
        # Save output
        with open(output_dir / "serial_ping.txt", "wb") as f:
            f.write(response + b"\n")
        
        assert response == b"PONG", f"Expected PONG, got {response}"
    
    def test_info_command(self, qemu_runner, output_dir):
        """Test info command"""
        boot_image = Path("../src/boot/boot.bin")
        qemu_runner.start(boot_image)
        
        # Wait for boot
        qemu_runner.read_until("Ready for commands", timeout=2)
        
        # Send info command
        qemu_runner.send('i')
        
        # Read response
        lines = []
        for _ in range(3):  # Expect 3 lines
            line = qemu_runner.read_line(timeout=1)
            if line:
                lines.append(line)
        
        # Save output
        with open(output_dir / "serial_info.txt", "wb") as f:
            for line in lines:
                f.write(line + b"\n")
        
        # Verify info
        assert any(b"AI-OS Bootloader" in line for line in lines)
        assert any(b"Version:" in line for line in lines)
        assert any(b"Memory:" in line for line in lines)
    
    def test_memory_command(self, qemu_runner, output_dir):
        """Test memory dump command"""
        boot_image = Path("../src/boot/boot.bin")
        qemu_runner.start(boot_image)
        
        # Wait for boot
        qemu_runner.read_until("Ready for commands", timeout=2)
        
        # Send memory command
        qemu_runner.send('m')
        
        # Read response (should be hex dump)
        lines = []
        for _ in range(3):  # Read a few lines
            line = qemu_runner.read_line(timeout=1)
            if line:
                lines.append(line)
        
        # Save output
        with open(output_dir / "serial_memory.txt", "wb") as f:
            for line in lines:
                f.write(line + b"\n")
        
        # Verify we got hex output
        assert len(lines) > 0, "No memory dump output"
        # First bytes should be 'FA' (cli instruction)
        assert b"FA" in lines[0], "Expected boot sector data"
    
    def test_self_test(self, qemu_runner, output_dir):
        """Test built-in self test"""
        boot_image = Path("../src/boot/boot.bin")
        qemu_runner.start(boot_image)
        
        # Wait for boot
        qemu_runner.read_until("Ready for commands", timeout=2)
        
        # Run tests
        qemu_runner.send('t')
        
        # Read response
        lines = qemu_runner.read_until("tests passed", timeout=2)
        
        # Save output  
        with open(output_dir / "serial_test.txt", "wb") as f:
            for line in lines:
                f.write(line + b"\n")
        
        # Verify tests passed
        assert any(b"All tests passed" in line for line in lines), "Self tests failed"
    
    def test_unknown_command(self, qemu_runner, output_dir):
        """Test error handling for unknown commands"""
        boot_image = Path("../src/boot/boot.bin")
        qemu_runner.start(boot_image)
        
        # Wait for boot
        qemu_runner.read_until("Ready for commands", timeout=2)
        
        # Send unknown command
        qemu_runner.send('x')
        
        # Read response
        response = qemu_runner.read_line(timeout=1)
        
        assert b"ERROR" in response, "No error for unknown command"
    
    def test_help_command(self, qemu_runner, output_dir):
        """Test help command"""
        boot_image = Path("../src/boot/boot.bin") 
        qemu_runner.start(boot_image)
        
        # Wait for boot
        qemu_runner.read_until("Ready for commands", timeout=2)
        
        # Send help
        qemu_runner.send('h')
        
        # Read help text
        lines = []
        for _ in range(8):  # Expect several lines
            line = qemu_runner.read_line(timeout=0.5)
            if line:
                lines.append(line)
        
        # Save output
        with open(output_dir / "serial_help.txt", "wb") as f:
            for line in lines:
                f.write(line + b"\n")
        
        # Verify help content
        assert any(b"Commands:" in line for line in lines)
        assert any(b"Ping" in line for line in lines)
        assert any(b"Info" in line for line in lines)