import time
import usb_hid
import board
import digitalio

from adafruit_hid import keyboard

class Layers:
    def __init__(self):
        self.layers = {}
        self.current_layer = (-1, -1)

    def new(self, coordinates: tuple, _map: dict):
        self.layers[coordinates] = _map

    def layer(self, coord: tuple):
        return self.layers[self.current_layer][coord]
    
    def change_layer(self, coordinates: tuple):
        self.current_layer = coordinates

    def get_current_layer(self):
        return self.current_layer

    def seek(self):
        return self.layers

# Define the rows and columns of the keyboard
columns = [board.GP0, board.GP1]
rows = [board.GP10, board.GP11]

# Initialize the rows and columns as data pins
rows = [digitalio.DigitalInOut(pin) for pin in rows]
columns = [digitalio.DigitalInOut(pin) for pin in columns]

kbd = keyboard.Keyboard(usb_hid.devices)

# Map coordinates to keys
_map = {(0, 0): [keyboard.Keycode.A], 
        (1, 0): [keyboard.Keycode.B], 
        (0, 1): [keyboard.Keycode.C]}

_map2 = {(0, 0): [keyboard.Keycode.SHIFT, keyboard.Keycode.A],
         (1, 0): [keyboard.Keycode.SHIFT, keyboard.Keycode.B],
         (0, 1): [keyboard.Keycode.SHIFT, keyboard.Keycode.C]}

layers = Layers()
layers.new((-1, -1), _map)
layers.new((1, 1), _map2)

layer_keys = [(1, 1)]

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
pressed_layer_key = ()

while True:
    # Iterate through each column
    for c, column in enumerate(columns):
        key = ()
        column.value = True
        # Iterate through each row
        for c2, row in enumerate(rows):
            # Get the coordinates of the key
            coordinates = (c, c2)

            # Check if a key is pressed
            if row.value:
                # Check if that key is a layer key
                if coordinates in layer_keys:
                    # Check if there is already a pressed layer key
                    # to avoid bugs and complications only one layer
                    # key should be active at a time
                    if not bool(pressed_layer_key):
                        # if it is a layer key, change the layer
                        # and also update the pressed_layer_key
                        layers.change_layer(coordinates)
                        pressed_layer_key = coordinates

                        # since its a layer key we do not need to process anymore
                        # so we continue to the next iteration
                        continue

                # Since the key is pressed, add the key to the combo
                key = layers.layer(coordinates)
                
                # Check if the key has been pressed before
                if coordinates not in pressed_keys:
                    # If it hasnt been pressed before, add it to the dictionary and send the key
                    # True and False means if the key is allowed to spam or not
                    # True -> allowed to spam, False -> not allowed to spam
                    pressed_keys[coordinates] = [time.monotonic(), False]
                    kbd.send(*key)
                else:
                    # If it has been pressed before, check if spammable is False
                    if pressed_keys[coordinates][1] == False:
                        # If spammable is false, check if enough time has passed
                        if time.monotonic() - pressed_keys[coordinates][0] > delay_before_spamming:
                            # If enough time has passed, send the key and update the spammable to True
                            pressed_keys[coordinates][1] = True
                            kbd.send(*key)
                    else:
                        # If spammable is True, all we have to do is just send the key (spam it)
                        kbd.send(*key)
            elif not row.value:
                # Since the code is infinitely looping, we check to see if the key is not pressed
                # If the key is not being pressed anymore, we check to see if it was in the dictionary previously
                # If it was in the dictionary, we must now remove it, to start the proccess all over again
                # .. this took me so much time for no reason :')
                if coordinates in pressed_keys:
                    del pressed_keys[coordinates]

                # if there is no key being pressed, we should check if any layer keys are being pressed
                # if not, we change the layer back to the default one and empty the pressed_layer_key
                if bool(pressed_layer_key):
                    layers.change_layer((-1, -1))
                    pressed_layer_key = ()

        column.value = False