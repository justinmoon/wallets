# m5stack

In this lesson we'll learn all the component pieces involved in building a hardware wallet using micropython on your m5stack.

## Install Micropython Firmware

(TODO: install silicon labs driver)

Make sure your virtual environment is activated. It contains packages for working with your m5stack.

Download the firmware (TODO: upload. TODO: how can i have this always fetch the latest release?). It's just a modded version of micropython with modules for working with bitcoin and m5stack display / buttons.

```
wget <TODO>
```

Figure out which port your m5stack is running on. It usually starts with `/dev/ttyUSB` on Unix, includes strin `COM` on Windows. If nothing shows up there is a problem with your serial driver. Get help in Slack.

```
python3 -m serial.tools.list_ports
/dev/ttyS0          
/dev/ttyUSB0  # this one
```

Flash firmware:

```
esptool.py --chip esp32 --port <port> --baud 460800 erase_flash
esptool.py --chip esp32 --port <port> --baud 460800 write_flash -z 0x1000 firmware.bin
``

## Hello World

The firmware we uploaded in the previous step is just a micropython interpreter, a C program that knows how to run micropython files. This is just like the `python3` program on your computer is a C program that can run python3 files.

Micropython is a subset of Python. Some of the python3 standard library is present, but much is missing. For example, our familiar `bytes.hex()` doesn't exist in micropython.

But much of it does work. The `asyncio` concurrency library is even there, with support for python's fancy new `async` / `await` syntax. We'll use this to run multiple concurrent routines on our hardware wallet (listen for messages coming from USB wire and button touches at the same time).

To get started we'll use [rshell](https://github.com/dhylands/rshell), which is a modified bash shell that allows you to `cp` files from your desktop to the m5stack, `edit` files on the m5stack, call `repl` to open a python shell in the m5stack, and more. Using the same `<port>` variable as in the previous step:

```
$ rshell -p /dev/ttyUSB0
Using buffer-size of 32
Connecting to /dev/ttyUSB0 (buffer-size 32)...
Trying to connect to REPL ... connected
Testing if ubinascii.unhexlify exists ... Y
Retrieving root directories ... /boot.py/ /main.py/ /key/
Setting time ... Aug 07, 2019 17:48:04
Evaluating board_name ... pyboard
Retrieving time epoch ... Jan 01, 2000
Welcome to rshell. Use Control-D (or the exit command) to exit rshell.
# FIXME: edit this prompt?
/home/justin/dev/teaching/wallets> 
```

Notice how your prompt has changed. This is the indicates that you're in rshell. You can always type `ctrl-c` or `ctrl-d` to exit rshell.

Let's enter a micropython REPL on the device:

```
/home/justin/dev/teaching/wallets> repl
Entering REPL. Use Control-X to exit.
>
MicroPython v1.11-97-gd821a27b5-dirty on 2019-07-25; ESP32 module with ESP32
Type "help()" for more information.
>>> 
```

Now we're in a micropython REPL inside rshell inside our normal shell. WICKED!

Let's try "Hello, world!"

```
>>> print('Hello, world!')
Hello, world!
```

That's python, alright!

There's a useful `help('modules')` command which will show you everything that's installed. Find a module that you're familiar with and test it out:

```
__init__          errno             mnemonic          ucryptolib
__main__          esp               neopixel          uctypes
_boot             esp32             network           uerrno
_ecc              flashbdev         ntptime           uhashlib
_onewire          framebuf          onewire           uhashlib
_thread           gc                os                uheapq
_webrepl          hashlib           pbkdf2            uio
apa106            hashlib           random            ujson
array             heapq             re                unittest
aswitch           hmac              select            uos
asyn              inisetup          socket            upip
binascii          io                ssl               upip_utarfile
bitcoin/__init__  json              struct            urandom
bitcoin/ecc       m5stack/__init__  sys               ure
bitcoin/hd        m5stack/fonts     tests/__init__    uselect
bitcoin/helper    m5stack/ili934/__init__             tests/data        usocket
bitcoin/mnemonic  m5stack/ili934/glcdfont             tests/test_ecc    ussl
bitcoin/op        m5stack/ili934/ili934xnew           tests/test_hd     ustruct
bitcoin/script    m5stack/ili934/tt14                 tests/test_tx     utime
bitcoin/tx        m5stack/ili934/tt24                 time              utimeq
btree             m5stack/ili934/tt32                 uasyncio/__init__ uwebsocket
builtins          m5stack/lcd       uasyncio/core     uzlib
cmath             m5stack/pins      uasyncio/queues   webrepl
collections       machine           uasyncio/synchro  webrepl_setup
dht               math              ubinascii         websocket_helper
ds18x20           micropython       ucollections      zlib
Plus any modules on the filesystem
>>> import hashlib
>>> hashlib.sha256(b'Hello, world!').digest()
b'1_[\xdbv\xd0x\xc4;\x8a\xc0\x06NJ\x01da+\x1f\xcew\xc8i4[\xfc\x94\xc7X\x94\xed\xd3'
>>> import time
>>> time.time
618515791
...
```

But I hope you also noticed the `bitcoin/` and `m5stack/` modules. These are from the custom firmware we're using. `bitcoin` is very similar to the `bedrock` library we've been using (modeled after the library from Jimmy Song's Programming Bitcoin book). `m5stack` has a driver for the display and some variables representing the different pins on the board (FIXME: explain pins).

Let's try a basic bitcoin operation:

```
>>> from bitcoin.ecc import PrivateKey
>>> PrivateKey(1, testnet=True).address()
'mrCDrCybB6J1vRfbwM5hemdJz73FwDBC8r'
```

Note: the APIs between `bitcoin` and `bedrock` differ slightly. `bedrock.ecc.PrivateKey.address` takes a `testnet` flag but `bitcoin.ecc.PrivateKey.address` doesn't. I'm working on this!

Let's use the other custom module: `m5stack`

```
>>> from m5stack import LCD
>>> lcd = LCD()
>>> lcd.print('Hello, world!')
```

You should see a tiny "Hello, world!" in the top left of your screen.

This is great, but if we restart the device it all goes away. There are two way to try this:
- "hard reset" by pressing the button next to the USB port on you m5stack.
- "soft reset" by hitting `ctrl-d` inside rshell.

To get code to run every time the device is turn on, we can't just enter it into the REPL. We need to put it in files on the device.

To do this we will exit the REPL by pressing `ctrl-x`. (Remember that one!). Now let's use rshell's `edit` command to make a `main.py` file on the device. This filename is what micropython attemts to run whenever it starts up.

```
/home/justin/dev/teaching/wallets> edit /pyboard/main.py
```

rshell mounts a `/pyboard` directory that corresponds to you m5stack (the first every micropython device was called "pyboard" and the name stuck).

At this point your `$EDITOR` should open. It's probably vim or nano, but I belive you can configure it to open GUI editors like sublime ...

Type the following into your editor and save.

```
from bitcoin.ecc import PrivateKey
from m5stack import LCD, fonts


def main():
    # create private key
    private_key = PrivateKey(1, testnet=True)
    address = private_key.address()

    # print associated address
    lcd = LCD()
    lcd.set_font(fonts.tt24)  # use a bigger font
    lcd.print(address)

if __name__ == '__main__':
    main()
```

If you restart your m5stack (by pressing the side button) you should see a bitcoin address printed on the screen. If you don't, there's probably a syntax error. You can debug by running `repl` and restarting the device (either side button, or `ctrl-d` now that we're back in REPL). Upon restarting, you should see a familiar python exception printed on the screen. For example, if you misspelled `private_key.adress()` (missing a "d") you would see:

```
>>> 
MPY: soft reboot
Traceback (most recent call last):
  File "main.py", line 16, in <module>
  File "main.py", line 8, in main
AttributeError: 'PrivateKey' object has no attribute 'adress'
MicroPython v1.11-97-gd821a27b5-dirty on 2019-07-25; ESP32 module with ESP32
Type "help()" for more information.
```

Even if you're program didn't have an error, perhaps add an error and try this just to practice debugging your m5stack. 

## Serial Communication

Now, let's try to send messages between our m5stack and our desktop computer. For this exercise, let's try another (more reliable) way to get code onto your m5stack. The trouble with calling `edit` is that your files are gone if your m5stack is erased. It's better to keep a canonical set of files in your git repo so you can't lose them, and _copy_ them onto the m5stack instead of directly writing them on the m5stack where no version control exists.

Write the following program into an `echo.py` file on in the current directory of your desktop machine (solution files are available in [examkples/](./examples)):

```
import time

from m5stack import LCD, fonts, color565

lcd = LCD()
lcd.set_font(fonts.tt24)
lcd.set_color(color565(0,50,250), color565(255,255,255))
lcd.erase()


while True:
    msg = input()
    lcd.print(msg)

```

Notes:
- We set a color for the foreground and background using `lcd.set_color(color565(...))`. You could try fiddling with the values to get different colors.
- You m5stack uses the "standard input" and "standard output" to communicate with its host machine over the USB wire. Therefore, you can read from the usb wire using `input()`
- We enter an endless loop which reads from "standard input" and prints to the LCD.

From rshell run the following to copy `echo.py` to your m5stack as `main.py`:

```
/home/justin/dev/teaching/wallets> cp echo.py /pyboard/main.py
```

If you restart the m5stack you'll notice that the background color did change which means the code at least kind of works, but we how can we sent it a message over the USB?

Once again, rshell can help us here. The `repl` command we've been using just connects over the serial USB port and sends keystrokes to the m5stack. When `main.py` exists, micropython takes over and opens a REPL. But when `main.py` doesn't end (e.g. our `while True`) loop, you keystrokes will be sent to the micropython program, accessible using `input()` and other less hacky ways we'll explore later.

```
/home/justin/dev/teaching/wallets> repl
Entering REPL. Use Control-X to exit.
>
MicroPython v1.11-97-gd821a27b5-dirty on 2019-07-25; ESP32 module with ESP32
Type "help()" for more information.
>>> ets Jun  8 2016 00:22:57

rst:0x1 (POWERON_RESET),boot:0x17 (SPI_FAST_FLASH_BOOT)
configsip: 0, SPIWP:0xee
clk_drv:0x00,q_drv:0x00,d_drv:0x00,cs0_drv:0x00,hd_drv:0x00,wp_drv:0x00
mode:DIO, clock div:2
load:0x3fff0018,len:4
load:0x3fff001c,len:4924
load:0x40078000,len:9404
ho 0 tail 12 room 4
load:0x40080400,len:6228
entry 0x400806ec
I (526) cpu_start: Pro cpu up.
I (526) cpu_start: Application information:
I (526) cpu_start: Compile time:     Jul  7 2019 23:21:41
I (530) cpu_start: ELF file SHA256:  0000000000000000...
I (536) cpu_start: ESP-IDF:          v3.3-beta1-694-g6b3da6b18
I (542) cpu_start: Starting app cpu, entry point is 0x40082b54
I (0) cpu_start: App cpu up.
I (552) heap_init: Initializing. RAM available for dynamic allocation:
I (559) heap_init: At 3FFAE6E0 len 00001920 (6 KiB): DRAM
I (565) heap_init: At 3FFBA018 len 00025FE8 (151 KiB): DRAM
I (572) heap_init: At 3FFE0440 len 00003AE0 (14 KiB): D/IRAM
I (578) heap_init: At 3FFE4350 len 0001BCB0 (111 KiB): D/IRAM
I (584) heap_init: At 400921FC len 0000DE04 (55 KiB): IRAM
I (591) cpu_start: Pro cpu start user code
I (161) cpu_start: Starting scheduler on PRO CPU.
I (0) cpu_start: Starting scheduler on APP CPU.
I (420) spi_master: Allocate TX buffer for DMA
I (430) spi_master: Allocate TX buffer for DMA
I (430) spi_master: Allocate TX buffer for DMA
```

A bunch of debugging output, but no micropython REPL prompt (`>>> `).

Try typing 'Hello, world!' into the terminal. It should appear on the display of your m5stack! Pretty impressive, huh?

Now see if you can figure out how to send a response back across the USB from micropython to and have it show up in rshell. Let say you entered in "Hello, world!"<enter> in rshell. You could have the m5stack reply "received 'Hello, world!'"


Hint: how do you send strings to "standard output" in normal python?

Answer:
.
.
.
(don't cheat)
.
.
.
Use the trust `print` command to send the response back to standard output and the out desktop machine.

Update `echo.py` with the following:

```
...

while True:
    msg = input()
    lcd.print(msg)
    res = 'Received: "{}"'.format(msg)
    print(res)
```

Restart the REPL to test it out. Hit `ctrl-x` to exit your old REPL session if it's still open, then reenter the REPL and start typing! 

```
/home/justin/dev/teaching/wallets> repl
Entering REPL. Use Control-X to exit.
>
MicroPython v1.11-97-gd821a27b5-dirty on 2019-07-25; ESP32 module with ESP32
Type "help()" for more information.
>>> 
>>> 
MPY: soft reboot
hi
Received: "hi"
friend
Received: "friend"
```

We now have 2 way communication over the USB port between our desktop and m5stack. feelsgood.gif!

Let's step back for a second. Our program has a main loop that can only handle messages over the serial port. But what if we want to have another loop which listens for button presses? We can't put code like `pressed = buttonA.is_pressed()` in our current look because the it will block serial messages and serial messages will be blocked by it.

Once again we need concurrency. There are two options:
1. threads
2. asyncio

We'll opt for the second option because it's generally easier to work with.

## Asyncio

### `counter.py`

Let's write a program using asyncio that prints just increments a counter, prints it to the screen, and sleeps for a second. This doesn't require any concurrency yet. But once we have it working we'll add another task that does the same thing but decrements a counter. Then we'll have 2 separate tasks running concurrently.

Enter the following code into a `counter.py` file on you desktop machine.

```
import uasyncio

from m5stack import LCD, fonts

lcd = LCD()
lcd.set_font(fonts.tt32)
lcd.erase()

async def increment():
    counter = 0
    while True:
        lcd.print('increment: {}'.format(counter)) 
        counter += 1
        await uasyncio.sleep(1)

def main():
    loop = uasyncio.get_event_loop()
    loop.create_task(increment())
    loop.run_forever()

if __name__ == '__main__':
    main()
```

Copy it over to the m5stack and restart (I'm going to stop telling you how to do this now. If you forget just scroll up).

You should see "Increment: i" lines printed out for increasing values of `i`.

See if you can figure out how to write a `decrement` function that does the same thing but subtracts instead of adding, and to run them both at the same time.

Answer:

```
...

async def decrement():
    counter = 0
    while True:
        lcd.print('decrement: {}'.format(counter)) 
        counter -= 1
        await uasyncio.sleep(1)

def main():
    ...
    loop.create_task(decrement())
    ...

```

If you copy `counter.py` over to the pyboard once again as `main.py` and restart, you should see both `Increment: i` and `Decrement: j` messages for increaing `i` values and decreasing `j` values.

### `buttons.py`

Now let's make a `buttons.py` demo that just responds to button presses:

```
import uasyncio
from aswitch import Pushbutton
from machine import Pin
from m5stack.pins import BUTTON_A_PIN, BUTTON_B_PIN, BUTTON_C_PIN
from m5stack import LCD, fonts

A = Pin(BUTTON_A_PIN, Pin.IN, Pin.PULL_UP)
B = Pin(BUTTON_B_PIN, Pin.IN, Pin.PULL_UP)
C = Pin(BUTTON_C_PIN, Pin.IN, Pin.PULL_UP)

lcd = LCD()
lcd.set_font(fonts.tt32)
lcd.erase()

def release_button(pin): 
    if pin == A:
        lcd.print("Button A")
    if pin == B:
        lcd.print("Button B")
    if pin == C:
        lcd.print("Button C")

async def button_manager():
    # TODO: these will need to be accessible from serial coroutine.
    # basically, global variables so that new behavior can be registered w/ .x_func()
    a = Pushbutton(A)
    a.release_func(release_button, (A,))
    b = Pushbutton(B)
    b.release_func(release_button, (B,))
    c = Pushbutton(C)
    c.release_func(release_button, (C,))

def main():
    loop = uasyncio.get_event_loop()
    loop.create_task(button_manager())
    loop.run_forever()

if __name__ == '__main__':
    main()
```

After uploading and running this you should be able should see "Button A" printed to the LCD when you hit the left button, "Button B" printed to the LCD when you hit the middle button, and "Button C" printed to the LCD when you press the right button.

### `io.py`

Let's make an asyncio version of the synchronous serial demo from earlier. Input the following into `io.py`:

```
import uasyncio
from m5stack import LCD, fonts
from sys import stdin, stdout

lcd = LCD()
lcd.set_font(fonts.tt32)
lcd.erase()

async def serial_manager():
    sreader = uasyncio.StreamReader(stdin)
    swriter = uasyncio.StreamWriter(stdout, {})  # TODO: what is this second param?
    while True:
        msg = await sreader.readline()
        res = 'Serial:' + msg.decode().strip()
        await swriter.awrite(res)
        lcd.print(res)

def main():
    loop = uasyncio.get_event_loop()
    loop.create_task(serial_manager())
    loop.run_forever()

if __name__ == '__main__':
    main()
```

If you re-upload the file and restart, you should be able to whatever you type into the rshell REPL should be echoed to the screen.

### `io_and_buttons.py`

Let's combine `buttons.py` and `io.py` and run both tasks at the same time:

```
import uasyncio
from aswitch import Pushbutton
from machine import Pin
from m5stack.pins import BUTTON_A_PIN, BUTTON_B_PIN, BUTTON_C_PIN
from m5stack import LCD, fonts
from sys import stdin, stdout

A = Pin(BUTTON_A_PIN, Pin.IN, Pin.PULL_UP)
B = Pin(BUTTON_B_PIN, Pin.IN, Pin.PULL_UP)
C = Pin(BUTTON_C_PIN, Pin.IN, Pin.PULL_UP)

lcd = LCD()
lcd.set_font(fonts.tt32)
lcd.erase()

def release_button(pin): 
    if pin == A:
        lcd.print("Button A")
    if pin == B:
        lcd.print("Button B")
    if pin == C:
        lcd.print("Button C")

async def button_manager():
    a = Pushbutton(A)
    a.release_func(release_button, (A,))
    b = Pushbutton(B)
    b.release_func(release_button, (B,))
    c = Pushbutton(C)
    c.release_func(release_button, (C,))

async def serial_manager():
    sreader = uasyncio.StreamReader(stdin)
    swriter = uasyncio.StreamWriter(stdout, {})
    while True:
        msg = await sreader.readline()
        msg = msg.decode()
        res = 'Serial: ' + msg
        await swriter.awrite(res)
        lcd.print(msg.strip('\n'))

def main():
    loop = uasyncio.get_event_loop()
    loop.create_task(button_manager())
    loop.create_task(serial_manager())
    loop.run_forever()

if __name__ == '__main__':
    main()

```

If you run this, you should be able to interact with the buttons and serial port (via rshell's `repl` command) at the same time. It's magic!

This type of logic is how we'll structure the business logic of our hardware wallet.

## PySerial

We've been using rshell's `repl` command so far to communicate with out device's serial port. But we'll need a python CLI to build a convenient wallet. Let's prototype that as well. Enter the following into a `cli.py` on your desktop machine: 

```
import sys
from serial import Serial
from serial.tools import list_ports

def find_port():
    '''figure out which port to connect to'''
    ports = list(list_ports.grep('CP2104 USB to UART Bridge Controller'))
    if len(ports) > 1:
        raise OSError("too many devices plugged in")
    elif len(ports) == 0:
        raise OSError("no device plugged in")
    else:
        return ports[0].device

def send_and_recv(msg):
    # this is the connection to the serial port
    ser =  Serial(find_port(), baudrate=115200)
    # send msg to device
    ser.write(msg.encode() + b'\n')
    # get response from device
    return ser.read_until(b'\n').strip(b'\n').decode()

def main():
    msg = ' '.join(sys.argv[1:])
    print(send_and_recv(msg))

if __name__ == '__main__':
    main()
```

You can run this with:

```
$ python cli.py orange coin good
Serial: orange coin good
$ python cli.py number go up
Serial: number go up
```

Everything after `cli.py` should show up on the display of your m5stack!

## Write To Disk & SD Card

A hardware wallet needs one last thing: the ability to write secrets to disk (risky because it can get erased) or to an SD card (safer). Let's make demos of both, starting with saving to disk:

Create a `disk.py` file for a demo of writing a number to the m5stack filesystem upon first run, then loading the number, printing it, and incrementing it after every subsequent run.

```
import os

from m5stack import LCD, fonts

lcd = LCD()
lcd.set_font(fonts.tt32)
lcd.erase()

filename = 'file.txt'

def load():
    with open(filename, 'r') as f:
        counter = int(f.read())
        lcd.print('Counter: {}'.format(counter))
        counter += 1
        save(counter=counter)

def save(counter=None):
    if counter is None:
        counter = 0
        lcd.print('Initialized')
    with open(filename, 'w') as f:
        f.write(str(counter))
        

if filename in os.listdir('/'):
    load()
else:
    save()
```

Just re-run the m5stack and watch the counter rise!

To do the same with an sd card, place an SD card into your m5stack, enter this into `sd.py` and run it:

```
import os
import machine

from m5stack import LCD, fonts

lcd = LCD()
lcd.set_font(fonts.tt32)
lcd.erase()

filename = 'file.txt'

def mount():
    sd = machine.SDCard(slot=3, mosi=23, miso=19, sck=18, cs=4)
    os.mount(sd, '/sd')

def load():
    with open('/sd/' + filename, 'r') as f:
        counter = int(f.read())
        counter += 1
        save(counter=counter)
        print('loaded', counter)

def save(counter=None):
    if counter is None:
        counter = 0
    with open('/sd/' + filename, 'w') as f:
        f.write(str(counter))
        print('saved', counter)

mount()

if filename in os.listdir('/sd'):
    load()
else:
    save()
```

For some reason the SD card works, but it bricks the display so we can only `print`. But if you run from the rshell `repl` you see that the counter increments every time. I'll try to fix this shortly ...
