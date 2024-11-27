#!/usr/bin/python3

#############################################################
#                                                           #
# File created by 0hStormy                                  #
#                                                           #
#############################################################

# Packages
import vlc
import os
import platform
import random
import sys
import select
import termios
import tty
import time
import json
from colorama import Fore, Style

global cmdInput
cmdInput = ""
global paused
paused = False
global homeFolder
homeFolder = os.path.expanduser('~')

# Color printing
def cprint(text, color):
    print(f"{color}{text}{colors.reset}")

def createConf():
    newConf = {
        "VolumeControl": 5,
        "DefaultVolume": 50,
        "Library": f"{homeFolder}/Music/",
        "QueueLength": 16,
        "Loop": False
    }
    with open(f"{homeFolder}/.bnap", "w") as f:
        converted = json.dumps(newConf)
        f.write(str(converted))

def read(key):
    with open(f"{homeFolder}/.bnap", "r") as f:
        dat = f.read()
        jsondat = json.loads(dat)
        print(jsondat)
        return jsondat[key]

def write(key, value):
    with open(f"{homeFolder}/.bnap", "r") as f:
        dat = f.read()
    with open(f"{homeFolder}/.bnap", "w") as f:
        jsondat = json.loads(dat)
        jsondat[key] = value
        f.write(json.dumps(jsondat))

def add(key, value):
    with open(f"{homeFolder}/.bnap", "r") as f:
        dat = f.read()
    with open(f"{homeFolder}/.bnap", "w") as f:
        jsondat = json.loads(dat)
        jsondat[key] = jsondat[key].append(value)
        f.write(json.dumps(jsondat))

# Determine clear command
def clear():
    if platform.system() == 'Windows':
        clearCMD = 'cls'
    else:
        clearCMD = 'clear'
    os.system(clearCMD)

def reloadSongs():
    songs = read("Library") # This is just an example

    with open(f"{homeFolder}/.bnapsongs", "w") as f:
        f.write("")

    with open(f"{homeFolder}/.bnapsongs", "a") as f:
        for path, subdirs, files in os.walk(songs):
            for name in files:
                if name.endswith((".png", ".jpg", ".jpeg")):
                    continue
                else:
                    f.write(f"{os.path.join(path, name)}[spl]")
                    print(f"Cached {name}")

def cliParse():
    if len(sys.argv) <= 1:
        return
    else:
        if os.path.isfile(sys.argv[1]) is True:
            play(sys.argv[1])
            sys.exit(0)
        else:
            print("Invalid file")
            sys.exit(1)

def play(file):
    player = vlc.MediaPlayer(f'file://{file}')
    player.play()
    counter = 0
    seconds = 0
    paused = False
    currentpause = False
    length = player.get_length() / 1000
    renderUI(file, seconds, length)

    while True:
        if currentpause is False:
            counter = counter + 1
            length = player.get_length() / 1000
            seconds = seconds + 1
            counter = 0
            global volume
            renderUI(file, seconds / 10, length)
        if seconds / 10 > length:
            if seconds > 1:
                print("Finished!")
                player.stop()
                break
        if paused is True:
            if currentpause is False:
                player.pause()
                currentpause = True
            else:
                player.pause()
                currentpause = False
            paused = False

        char = get_nonblocking_input()
        if char == "q":
            clear()
            sys.exit(0)
        if char == "z":
            player.stop()
            print("Choosing new song...")
            time.sleep(0.25)
            return
        if char == " ":
            paused = True
        if char == "=":
            volume = volume + read("VolumeControl")
            player.audio_set_volume(volume)
        if char == "-":
            volume = volume - read("VolumeControl")
            player.audio_set_volume(volume)
        if char == "l":
            global looping
            if looping is False:
                looping = True
            else:
                looping = False

def progressBar(current, end):
    terminalY = os.get_terminal_size().lines
    terminalX = os.get_terminal_size().columns
    int(terminalX)
    int(terminalY)
    try:
         cprint(("|" * round(int(current) / (end / terminalX))), colors.purple)
    except ZeroDivisionError:
        print("...")

def get_nonblocking_input():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        if ready:
            return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None


def renderUI(file, seconds, length):
        clear()
        cprint(f"Playing {os.path.basename(file)}", colors.green)
        print(f"{seconds}s/{round(length)}s")
        print(f"Volume: {volume}")
        print(f"Looping: {looping}")
        progressBar(seconds, length)
        index = 0
        for songs in queue:
            index = index + 1
            cprint(f"{index}: {os.path.basename(songs)}", colors.blue)

def getSongs():
    with open(f"{homeFolder}/.bnapsongs", "r") as f: 
        fullList = f.read()
        splitList = fullList.split("[spl]")
        del splitList[-1]
        return splitList

def addToQueue(amount):
    for i in range(amount):
        splList = getSongs()
        queue.append(random.choice(splList))

# Init Vars
class colors:
    red = Fore.LIGHTRED_EX
    green = Fore.LIGHTGREEN_EX
    blue = Fore.LIGHTBLUE_EX
    purple = Fore.MAGENTA
    yellow = Fore.LIGHTYELLOW_EX
    reset = Style.RESET_ALL

if os.path.isfile(f"{homeFolder}/.bnap") is False:
    createConf()
reloadSongs()

queue = []

global looping
looping = read("Loop")

global volume
volume = read("DefaultVolume")

cliParse()

addToQueue(read("QueueLength"))

while True:
    current = queue[0]
    if looping is False:
        queue.pop(0)
        addToQueue(1)
    play(current)
