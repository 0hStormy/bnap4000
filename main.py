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
import time
import json
from colorama import Fore, Style

# Check what modules to use for input
if platform.system() == "Windows": # Windows
    import msvcrt
else: # Posix
    import select
    import termios
    import tty

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
        "Loop": False,
        "skipKey": "z",
        "pauseKey": " ",
        "volUpKey": "=",
        "volDownKey": "-",
        "loopKey": "l",
        "exitKey": "q"
    }
    with open(f"{homeFolder}/.bnap/config.json", "w") as f:
        converted = json.dumps(newConf, indent=4)
        f.write(str(converted))

def read(key):
    with open(f"{homeFolder}/.bnap/config.json", "r") as f:
        dat = f.read()
        jsondat = json.loads(dat)
        return jsondat[key]

def write(key, value):
    with open(f"{homeFolder}/.bnap/config.json", "r") as f:
        dat = f.read()
    with open(f"{homeFolder}/.bnap/config.json", "w") as f:
        jsondat = json.loads(dat)
        jsondat[key] = value
        f.write(json.dumps(jsondat))

def add(key, value):
    with open(f"{homeFolder}/.bnap/config.json", "r") as f:
        dat = f.read()
    with open(f"{homeFolder}/.bnap/config.json", "w") as f:
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

    with open(f"{homeFolder}/.bnap/songs", "w") as f:
        f.write("")

    with open(f"{homeFolder}/.bnap/songs", "a") as f:
        for path, subdirs, files in os.walk(songs):
            for name in files:
                if name.endswith((".png", ".jpg", ".jpeg", ".ini")):
                    continue
                else:
                    f.write(f"{os.path.join(path, name)}[spl]")

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
    if platform.system() == "Windows":
        prefix = ""
    else: # Posix
        prefix = "file://"
    player = vlc.MediaPlayer(f'{prefix}{file}')
    player.play()
    counter = 0
    seconds = 0
    interval = 0.1
    nextTime = time.time() + interval
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
        if char == keybinds.exitKey:
            clear()
            sys.exit(0)
        if char == keybinds.skip:
            player.stop()
            print("Choosing new song...")
            return
        if char == keybinds.pause:
            paused = True
        if char == keybinds.volUp:
            volume = volume + read("VolumeControl")
            player.audio_set_volume(volume)
        if char == keybinds.volDown:
            volume = volume - read("VolumeControl")
            player.audio_set_volume(volume)
        if char == keybinds.loop:
            global looping
            if looping is False:
                looping = True
            else:
                looping = False
        time.sleep(max(0, nextTime - time.time()))
        nextTime += interval

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
    if platform.system() == "Windows": # Windows
        if msvcrt.kbhit():
            return msvcrt.getch().decode("utf-8")
    else: # Posix
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
    with open(f"{homeFolder}/.bnap/songs", "r") as f: 
        fullList = f.read()
        splitList = fullList.split("[spl]")
        del splitList[-1]
        return splitList

def addToQueue(amount):
    for i in range(amount):
        splList = getSongs()
        queue.append(random.choice(splList))

def newUser():
    clear()
    cprint("Welcome to bnap400! Let's answer a couple questions to get started!", colors.purple)
    cprint("The config file is located in ~/.bnap/config.json if you ever need to change something.", colors.purple)
    musicFolder = input("Music library location (leave blank for default): ")
    if musicFolder != "":
        write("Library", musicFolder)
        cprint(f"Set music library to {musicFolder}", colors.green)
    else:
        cprint(f"Set music library to {read("Library")}", colors.green)
    defaultVolume = input("Default volume (0-100): ")
    if defaultVolume != "":
        write("DefaultVolume", int(defaultVolume))
        cprint(f"Set default volume to {defaultVolume}%", colors.green)
    else:
        cprint(f"Set default volume to {read("DefaultVolume")}%", colors.green)
    input("Setup complete! Press enter to start bnap4000.")

# Init Colors
class colors:
    red = Fore.LIGHTRED_EX
    green = Fore.LIGHTGREEN_EX
    blue = Fore.LIGHTBLUE_EX
    purple = Fore.MAGENTA
    yellow = Fore.LIGHTYELLOW_EX
    reset = Style.RESET_ALL

# Create config
if os.path.isfile(f"{homeFolder}/.bnap/config.json") is False:
    if os.path.isdir(f"{homeFolder}/.bnap/") is False:
        os.makedirs(f"{homeFolder}/.bnap/")
    createConf()
    newUser()

# Init Keybinds
class keybinds:
    skip = read("skipKey")
    pause = read("pauseKey")
    volUp = read("volUpKey")
    volDown = read("volDownKey")
    loop = read("loopKey")
    exitKey = read("exitKey")


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
