#!/usr/bin/bash

# Check if there is no install location
if [$1 = ""]; then
    echo Please provide a install location. Ex: /usr/local/bin/
    exit 1
fi

# Install packages from pip
python -m pip install python-vlc

echo Depending on where you install, the builder might ask for sudo permissions.

# Remove old version of banp
sudo rm $1/bnap

# Move banp to /usr/local/bin
sudo cp main.py $1/bnap
sudo chmod +x $1/bnap

# Run
bnap
