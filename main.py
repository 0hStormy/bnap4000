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
        "Locale": "en_US",
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

def locale(key):
    try:
        with open(f"{Path(__file__).parent / "lang" / read("Locale")}.json", "r") as f:
            dat = f.read()
            jsondat = json.loads(dat)
            return jsondat[key]
    except KeyError:
        return "Missing Locale, something has probably gone very wrong!"

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
            play(sys.argv[1], "direct")
            sys.exit(0)
        else:
            print("Invalid file")
            sys.exit(1)

def startswithnum(num):
    try:
        num = int(num)
        return True
    except ValueError:
        return False

def play(file, playbackMode="normal"):
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

    renderUI(file, seconds, length, playbackMode)

    while True:
        if currentpause is False:
            if counter == 10:
                counter = counter + 1
                length = player.get_length() / 1000
                seconds = seconds + 1
                counter = 0
                renderUI(file, seconds, length, playbackMode)
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
            return
        if char == keybinds.restart:
            player.stop()
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
                renderUI(file, seconds, length, playbackMode)
            paused = False
        if char == keybinds.volUp:
            volume = volume + read("VolumeControl")
            player.audio_set_volume(volume)
            renderUI(file, seconds, length, playbackMode)
        if char == keybinds.volDown:
            volume = volume - read("VolumeControl")
            player.audio_set_volume(volume)
            renderUI(file, seconds, length, playbackMode)
        if char == keybinds.streamKey:
            player.stop()
            return "netStream"
        if char == keybinds.loop:
            global looping
            if looping is False:
                looping = True
            else:
                looping = False
            renderUI(file, seconds, length, playbackMode)
        if char == keybinds.navKey:
            paused = True
            currentpause = True
            player.stop()
            songNav()
            currentpause = False
            player.play()

        if currentpause is False:
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
    print(f"{colors.white}{icons.line * terminalX}")

def renderDir(dir, index):
    try:
        contents = os.listdir(dir)
    except NotADirectoryError:
        play(dir, "direct")
    i = 0
    for file in contents:
        if file.endswith((".png", ".jpg", ".jpeg", ".ini")):
                    continue
        else:
            if i == index:
                cprint(f"{i + 1}: {file}", colors.blue)
                selected = file
            else:
                cprint(f"{i + 1}: {file}", colors.white)
            i = i + 1
    return selected

def songNav():
    dirIndex = 0
    cwd = read("Library")
    while True:
        clear()
        cprint(locale("ui.songSelect"), colors.green)
        drawLine()
        selectedAlbum = renderDir(cwd, dirIndex)
        drawLine()
        cmd = input(":")
        if cmd == "q": # Quit
            break

        elif cmd == "": # Confirm
            dirIndex = 0
            cwd = cwd + f"/{selectedAlbum}"
            
        elif cmd == "..":
            cwd = os.path.join(os.path.dirname(cwd), '..')

        elif cmd == "pa":
            global queue
            queue = []
            totalSongs = 0
            contents = os.listdir(f"{cwd}/{selectedAlbum}/")
            for file in contents:
                if file.endswith((".png", ".jpg", ".jpeg", ".ini")):
                    continue
                else:
                    totalSongs += 1
                    queue.append(f"{cwd}/{selectedAlbum}/{file}")
            queue.sort()
            print(read("QueueLength") - totalSongs)
            addToQueue(read("QueueLength") - totalSongs)
            playLoop()

        elif startswithnum(cmd):
            dirIndex = (int(cmd) - 1)

def renderUI(file, seconds, length, playbackMode):
        clear()
        global currentpause
        if currentpause is True:
            pauseIcon = icons.paused
        else:
            pauseIcon = icons.unpaused
        global netStream
        if netStream is True:
            cprint(f"{icons.musicNote}{locale("ui.station")}: {file}", colors.green)
        else:
            cprint(f"{icons.musicNote}{locale("ui.song")}: {file}", colors.green)
        print(f"{pauseIcon}{seconds}s/{round(length)}s")
        print(f"{icons.vol}{locale("ui.volume")}: {volume}")
        print(f"{icons.loop}{locale("ui.looping")}: {looping}")
        drawLine()
        progressBar(seconds, length)
        drawLine()
        index = 0
        if playbackMode != "direct":
            print(f"{icons.queue}{locale("ui.queue")}:")
            for songs in queue:
                index = index + 1
                songs = Path(songs).stem
                cprint(f"   {index}: {os.path.basename(songs)}", colors.blue)
            drawLine()

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
    cprint(locale("welcome.welcome"), colors.purple)
    cprint(locale("welcome.confignote"), colors.purple)
    musicFolder = input(f"{locale("welcome.library")}: ")
    if musicFolder != "":
        write("Library", musicFolder)
        cprint(f"{locale("welcome.musLib")} {musicFolder}", colors.green)
    else:
        cprint(f"{locale("welcome.musLib")}: {read("Library")}", colors.green)
    defaultVolume = input(f"{locale("welcome.volume")}: ")
    if defaultVolume != "":
        write("DefaultVolume", int(defaultVolume))
        cprint(f"{locale("welcome.newVol")} {defaultVolume}%", colors.green)
    else:
        cprint(f"{locale("welcome.newVol")} {read("DefaultVolume")}%", colors.green)
    nerdFont = input(f"{locale("welcome.nerdfont")}: ")
    if nerdFont == "y":
        write("NerdFontSupport", True)
        cprint(locale("welcome.nerdOn"), colors.green)
    else:
        cprint(locale("welcome.nerdOff"), colors.green)
    input(locale("welcome.complete"))

def playLoop():
    endCode = ""
    while True:
        mode = "normal"
        if looping is False:
            if endCode != "restart":
                current = queue[0]
                queue.pop(0)
                addToQueue(1)
        if endCode == "netStream":
            current = input(f"{locale("ui.iradio")}: ")
            mode = "net"
        endCode = play(current, mode)

# Init Colors
class colors:
    red = Fore.LIGHTRED_EX
    green = Fore.LIGHTGREEN_EX
    blue = Fore.LIGHTBLUE_EX
    purple = Fore.MAGENTA
    yellow = Fore.LIGHTYELLOW_EX
    white = Fore.WHITE
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
    navKey = "s"

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

global queue
queue = []
endCode = ""

global looping
looping = read("Loop")

global volume
volume = read("DefaultVolume")

cliParse()

addToQueue(read("QueueLength"))

playLoop()