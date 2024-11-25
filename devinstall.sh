#!/usr/bin/bash

# Check if there is no install location
if [$1 = ""]; then
    echo Please provide a install location. Ex: /usr/local/bin/
    exit 1
fi

# Start build
nuitka --standalone --onefile main.py
rm -rf main.dist/
rm -rf main.onefile-build/
rm -rf main.build/

echo Depending on where you install, the builder might ask for sudo permissions.

# Remove old version of banp
sudo rm $1/bnap

# Move banp to /usr/local/bin
sudo cp main.bin $1/bnap
sudo chmod +x $1/bnap
rm main.bin

# Run
bnap
