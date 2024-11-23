import vlc
import os
import platform
import random
import sys
import select
import termios
import tty
import time

global cmdInput
cmdInput = ""
global paused
paused = False

# Determine clear command
def clear():
    if platform.system() == 'Windows':
        clearCMD = 'cls'
    else:
        clearCMD = 'clear'
    os.system(clearCMD)

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
            exit(0)
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
            volume = volume + 5
            player.audio_set_volume(volume)
        if char == "-":
            volume = volume - 5
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

while True:
    songs = "/home/stormy/Music/Library/" # This is just an example
    extra = ""
    while True:
        try:
            new = random.choice(os.listdir(f"{songs}{extra}"))
        except NotADirectoryError:
            break    
        extra = extra + "/" + new
        try:
            if os.path.isdir(new) is True:
                continue
        except NotADirectoryError:
            break
    play(f"{songs}{extra}")