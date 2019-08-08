import uasyncio

from m5stack import LCD, fonts

lcd = LCD()
lcd.set_font(fonts.tt32)
lcd.erase()

async def decrement():
    counter = 0
    while True:
        lcd.print('decrement: {}'.format(counter)) 
        counter -= 1
        await uasyncio.sleep(1)

async def increment():
    counter = 0
    while True:
        lcd.print('increment: {}'.format(counter)) 
        counter += 1
        await uasyncio.sleep(1)

def main():
    loop = uasyncio.get_event_loop()
    loop.create_task(increment())
    loop.create_task(decrement())
    loop.run_forever()

if __name__ == '__main__':
    main()

