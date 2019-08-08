import uos

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
        

if filename in uos.listdir('/'):
    load()
else:
    save()
