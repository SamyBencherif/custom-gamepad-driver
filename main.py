import usb
import time

"""
Thanks to https://www.partsnotincluded.com/understanding-the-xbox-360-wired-controllers-usb-data/
"""

gamepad = usb.core.find(idVendor=0x045e, idProduct=0x028e)

if gamepad is None:
  print("Waiting for gamepad...")
  while gamepad is None:
    gamepad = usb.core.find(idVendor=0x045e, idProduct=0x028e)
    time.sleep(.1)


gamepad.set_configuration()

while True:
  B = gamepad.read(0x81, 20)

  # ignore messages I don't understand
  if B[0] != 0 or B[1] != 20:
    continue

  print("[A] :", ((B[3]>>4)&1))
