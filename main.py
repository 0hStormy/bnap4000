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
from pathlib import Path
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
global renderedLines
renderedLines = 0
global openPrompt
openPrompt = False

# Color printing
def cprint(text, color):
    print(f"{color}{text}{colors.reset}")
    global renderedLines
    renderedLines = renderedLines + 1

def createConf():
    newConf = {
        "VolumeControl": 5,
        "DefaultVolume": 50,
        "Library": f"{homeFolder}/Music/",
        "QueueLength": 16,
        "NerdFontSupport": False,
        "Loop": False,
        "skipKey": "z",
        "pauseKey": " ",
        "volUpKey": "=",
        "volDownKey": "-",
        "restartKey": "x",
        "loopKey": "l",
        "exitKey": "q",
        "streamKey": "n"
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
    global renderedLines
    renderedLines = 0

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
    global netStream
    if not file.startswith("https://"):
        if platform.system() == "Windows":
            prefix = ""
        else: # Posix
            prefix = "file://"
        netStream = False
    else:
        prefix = ""
        netStream = True
    player = vlc.MediaPlayer(f'{prefix}{file}')
    player.play()
    counter = 0
    seconds = 0
    interval = 0.1
    nextTime = time.time() + interval
    paused = False
    global currentpause
    currentpause = False
    length = player.get_length() / 1000

    if netStream is False:
        file = os.path.basename(file)
        file = Path(file).stem
    else:
        file = file.removeprefix("https://")

    renderUI(file, seconds, length)

    while True:
        if currentpause is False:
            if counter == 10:
                counter = counter + 1
                length = player.get_length() / 1000
                seconds = seconds + 1
                counter = 0
                renderUI(file, seconds, length)
            global volume
        if netStream is False:
            if seconds > length:
                if seconds > 2:
                    print("Finished!")
                    player.stop()
                    break
            paused = False

        char = get_nonblocking_input()
        if char == keybinds.exitKey:
            clear()
            sys.exit(0)
        if char == keybinds.skip:
            player.stop()
            print("Choosing new song...")
            return
        if char == keybinds.restart:
            player.stop()
            print("Restarting song")
            return "restart"
        if char == keybinds.pause:
            paused = True
            if paused is True:
                print(paused, currentpause)
                if currentpause is False:
                    player.pause()
                    currentpause = True
                else:
                    player.pause()
                    currentpause = False
                renderUI(file, seconds, length)
            paused = False
        if char == keybinds.volUp:
            volume = volume + read("VolumeControl")
            player.audio_set_volume(volume)
            renderUI(file, seconds, length)
        if char == keybinds.volDown:
            volume = volume - read("VolumeControl")
            player.audio_set_volume(volume)
            renderUI(file, seconds, length)
        if char == keybinds.streamKey:
            player.stop()
            return "netStream"
        if char == keybinds.loop:
            global looping
            if looping is False:
                looping = True
            else:
                looping = False
            renderUI(file, seconds, length)

        time.sleep(max(0, nextTime - time.time()))
        nextTime += interval
        counter = counter + 1

def progressBar(current, end):
    terminalX = os.get_terminal_size().columns
    int(terminalX)
    try:
        progressNum = round(int(current) / (end / terminalX))
        print((f"{colors.purple}{icons.square}" * progressNum ) + (f"{colors.reset}{icons.square}" * (terminalX - progressNum)))
    except ZeroDivisionError:
        print("...")

def drawLine():
    terminalX = os.get_terminal_size().columns
    print(icons.line * terminalX)

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
        global currentpause
        if currentpause is True:
            pauseIcon = icons.paused
        else:
            pauseIcon = icons.unpaused
        global netStream
        if netStream is True:
            cprint(f"{icons.musicNote}Station: {file}", colors.green)
        else:
            cprint(f"{icons.musicNote}Song: {file}", colors.green)
        print(f"{pauseIcon}{seconds}s/{round(length)}s")
        print(f"{icons.vol}Volume: {volume}")
        print(f"{icons.loop}Looping: {looping}")
        drawLine()
        progressBar(seconds, length)
        drawLine()
        index = 0
        print(f"{icons.queue}Queue:")
        for songs in queue:
            index = index + 1
            songs = Path(songs).stem
            cprint(f"   {index}: {os.path.basename(songs)}", colors.blue)
        drawLine()

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
    nerdFont = input("Do you want Nerd Font icons? This requires a Nerd Font! (y/N): ")
    if nerdFont == "y":
        write("NerdFontSupport", True)
        cprint("Set Nerd Font support on!", colors.green)
    else:
        cprint("Set Nerd Font support off!", colors.green)
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
    restart = read("restartKey")
    loop = read("loopKey")
    exitKey = read("exitKey")
    streamKey = read("streamKey")

class icons:
    if read("NerdFontSupport") is True:
        paused = "󰐊 "
        unpaused = "󰏤 "
        musicNote = " "
        vol = "󰕾 "
        loop = "󱃔 "
        queue = "󱕱 "
        square = "󰝤"
        line = ""
    else:
        paused = "|> "
        unpaused = "|| "
        musicNote = ""
        vol = ""
        loop = ""
        queue = ""
        square = "#"
        line = "-"

reloadSongs()

queue = []
endCode = ""

global looping
looping = read("Loop")

global volume
volume = read("DefaultVolume")

cliParse()

addToQueue(read("QueueLength"))

while True:
    if looping is False:
        if endCode != "restart":
            current = queue[0]
            queue.pop(0)
            addToQueue(1)
    if endCode == "netStream":
        current = input("Internet Radio URL: ")
    endCode = play(current)
