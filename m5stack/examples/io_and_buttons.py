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
    swriter = uasyncio.StreamWriter(stdout, {})  # TODO: what is this second param?
    while True:
        msg = await sreader.readline()
        msg = msg.decode()
        lcd.print(msg.strip('\n'))
        res = 'Serial: ' + msg
        await swriter.awrite(res)

def main():
    loop = uasyncio.get_event_loop()
    loop.create_task(button_manager())
    loop.create_task(serial_manager())
    loop.run_forever()

if __name__ == '__main__':
    main()
