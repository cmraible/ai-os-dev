"""Test simple echo functionality"""

import pytest
from pathlib import Path

class TestEcho:
    """Test the simple test bootloader"""
    
    def test_echo_boot(self, qemu_runner, output_dir):
        """Test that test bootloader starts correctly"""
        boot_image = Path("../src/boot/test_boot.bin")
        assert boot_image.exists(), "Test boot image not found"
        
        qemu_runner.start(boot_image)
        
        # Should see test marker
        lines = qemu_runner.read_until("TEST_BOOT_OK", timeout=2)
        assert any(b"TEST_BOOT_OK" in line for line in lines)
    
    def test_echo_functionality(self, qemu_runner, output_dir):
        """Test echo functionality"""
        boot_image = Path("../src/boot/test_boot.bin")
        qemu_runner.start(boot_image)
        
        # Wait for boot
        qemu_runner.read_until("TEST_BOOT_OK", timeout=2)
        
        # Test echo
        test_chars = ['a', 'b', 'c', '1', '2', '3']
        for char in test_chars:
            qemu_runner.send(char)
            response = qemu_runner.read_line(timeout=0.5)
            assert response == char.encode(), f"Echo failed for {char}"
    
    def test_quit_command(self, qemu_runner, output_dir):
        """Test quit command"""
        boot_image = Path("../src/boot/test_boot.bin")
        qemu_runner.start(boot_image)
        
        # Wait for boot
        qemu_runner.read_until("TEST_BOOT_OK", timeout=2)
        
        # Send quit
        qemu_runner.send('q')
        
        # Should see quit message
        response = qemu_runner.read_line(timeout=1)
        assert b"QUIT_OK" in response