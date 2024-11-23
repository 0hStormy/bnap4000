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


global cmdInput
cmdInput = ""
global paused
paused = False

def createConf():
    newSave = {
        "VolumeControl": 5,
        "Library": "~/Music/"
    }
    with open("config.json", "w") as f:
        f.write(str(newSave).replace("'", '"'))

def read(key):
    with open("config.json", "r") as f:
        dat = f.read()
        jsondat = json.loads(dat)
        return jsondat[key]

def write(key, value):
    with open("config.json", "r") as f:
        dat = f.read()
    with open("config.json", "w") as f:
        jsondat = json.loads(dat)
        jsondat[key] = value
        f.write(json.dumps(jsondat))

def add(key, value):
    with open("config.json", "r") as f:
        dat = f.read()
    with open("config.json", "w") as f:
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

    with open("songs.bnl", "w") as f:
        f.write("")

    with open("songs.bnl", "a") as f:
        for path, subdirs, files in os.walk(songs):
            for name in files:
                if name.endswith((".png", ".jpg", ".jpeg")):
                    continue
                else:
                    f.write(f"{os.path.join(path, name)}[spl]")
                    print(f"Cached {name}")


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

def progressBar(current, end):
    terminalY = os.get_terminal_size().lines
    terminalX = os.get_terminal_size().columns
    int(terminalX)
    int(terminalY)
    try:
         print(("|" * round(int(current) / (end / terminalX))))
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
        print(f"Playing {os.path.basename(file)}")
        print(f"{seconds}s/{round(length)}s")
        print(f"Volume: {volume}")
        progressBar(seconds, length)

global volume
volume = 50

if os.path.isfile("config.json") is False:
    createConf()
reloadSongs()

while True:
    with open("songs.bnl", "r") as f:
        fullList = f.read()
        splitList = fullList.split("[spl]")
    play(random.choice(splitList))