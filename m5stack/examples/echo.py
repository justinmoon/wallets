from m5stack import LCD, fonts, color565

lcd = LCD()
lcd.set_font(fonts.tt24)
lcd.set_color(color565(0,50,250), color565(255,255,255))
lcd.erase()

while True:
    msg = input()
    lcd.print(msg)
    res = 'Received: "{}"'.format(msg)
    print(res)
