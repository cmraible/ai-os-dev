#!/bin/bash
# Installation script for AI OS development environment

echo "Setting up AI OS development environment..."

# Check OS and install dependencies
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo apt-get update
    sudo apt-get install -y qemu-system-x86 nasm build-essential python3-pip
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if ! command -v brew &> /dev/null; then
        echo "Please install Homebrew first"
        exit 1
    fi
    brew install qemu nasm python3
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Install Python dependencies
pip3 install -r requirements.txt

echo "Installation complete!"
echo "Run 'python3 setup.py' to start the development environment"