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

