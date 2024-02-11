import time
import usb_hid
import board
import digitalio

from adafruit_hid import keyboard

columns = [board.GP0, board.GP1]
rows = [board.GP10, board.GP11]

rows = [digitalio.DigitalInOut(pin) for pin in rows]
columns = [digitalio.DigitalInOut(pin) for pin in columns]

kbd = keyboard.Keyboard(usb_hid.devices)

# Map coordinates to keys
_map = {(0, 0): keyboard.Keycode.A, 
        (1, 0): keyboard.Keycode.B, 
        (0, 1): keyboard.Keycode.C, 
        (1, 1): keyboard.Keycode.D}


# Set the direction and pull of each row pin
for counter, pin in enumerate(rows):
    pin.direction = digitalio.Direction.INPUT
    pin.pull = digitalio.Pull.DOWN
    rows[counter] = pin

# Set the direction of each column pin
for counter, pin in enumerate(columns):
    pin.direction = digitalio.Direction.OUTPUT
    columns[counter] = pin

delay_before_spamming = 0.3 #second(s)
pressed_keys = {}

while True:
    # Iterate through each column
    for c, column in enumerate(columns):
        combo = []
        column.value = True
        # Iterate through each row
        for c2, row in enumerate(rows):

            # Get the coordinates of the key
            coordinates = (c, c2)

            # Check if a key is pressed
            if row.value:
                # Since the key is pressed, add the key to the combo
                combo.append(_map[coordinates])
                
                # Check if the key has been pressed before
                if coordinates not in pressed_keys:
                    # If it hasnt been pressed before, add it to the dictionary and send the key
                    # True and False means if the key is allowed to spam or not
                    # True -> allowed to spam, False -> not allowed to spam
                    pressed_keys[coordinates] = [time.monotonic(), False]
                    kbd.send(*combo)
                else:
                    # If it has been pressed before, check if spammable is False
                    if pressed_keys[coordinates][1] == False:
                        # If spammable is false, check if enough time has passed
                        if time.monotonic() - pressed_keys[coordinates][0] > delay_before_spamming:
                            # If enough time has passed, send the key and update the spammable to True
                            pressed_keys[coordinates][1] = True
                            kbd.send(*combo)
                    else:
                        # If spammable is True, all we have to do is just send the key (spam it)
                        kbd.send(*combo)
            elif not row.value:
                # Since the code is infinitely looping, we check to see if the key is not pressed
                # If the key is not being pressed anymore, we check to see if it was in the dictionary previously
                # If it was in the dictionary, we must now remove it, to start the proccess all over again
                # .. this took me so much time for no reason :')
                if coordinates in pressed_keys:
                    del pressed_keys[coordinates]
            # Check if a key is pressed and key is already pressed
        column.value = False

