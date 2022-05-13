
import os
import time
import threading

# Preamble:
# This project will work on UNIX-like systems only. 
# Linux, BSD, even macOS, you are in luck.

# If you really need to work in Windows, you must find a project
# that maps devices to a virtual /dev -- or rework the device
# acquisition phase of this program.

# Amendment: Can be adapted to Windows using pyserial

#######################################################################
#                                                                     # 
#  Step 1: Determine which device to listen to...                     # 
#                                                                     # 
#######################################################################

# It seems like gamepad controllers are typically mapped to:
  # /dev/input/js...

# If you already know the filemapped I/O path of your device enter 
# it here:
device = ""

# Otherwise I will look for it myself,
def discoverJoystick():
  if not os.path.exists("/dev"):
    print("This does not seem to be a UNIX-like system.")
    return []
  if not os.path.exists("/dev/input"):
    print("I do not see any filemapped input devices.")
    return []
  joysticks = []
  for d in os.listdir("/dev/input"):
    if d.startswith("js"):
      joysticks.append("/dev/input/" + str(d))
  if not joysticks:
    print("I did not find any devices that look like JoySticks.")
    idev = os.listdir("/dev/input")
    start = time.time()
    print("Try unplugging and replugging the device to help me find it... (10 sec)")
    while len(idev) == len(os.listdir("/dev/input")) and \
      time.time() - start < 10:
      time.sleep(.1)
    idev2 = os.listdir("/dev/input")
    if len(idev) != len(idev2):
      print("I detected a change.")
      diff=[]
      for i in idev:
        if not i in idev2:
          diff += [str(i) + " was unplugged."]
      for i in idev2:
        if not i in idev:
          diff += [str(i) + " was plugged in."]
    else:
      print("I could not detect anything.")
      return []
  else:
    # I've found at least one joystick
    return joysticks

def timeoutReadByte(dev, timeout):
  out = [None]
  def process(out):
    out[0] = dev.read(1)

  p = threading.Thread(target=process, args=(out,))
  p.setDaemon(True)
  p.start()
  start = time.time()
  while p.is_alive() and time.time()-start < timeout:
    time.sleep(50/1000) # inperceptible to humans <150ms
  return out[0]

# waits for inactivity before returning, suitable for buttons
def scan(inactivity=.1, noempty=True, printdata=False):
  seq = []
  while 1:
    for i in range(10):
      if not seq:
        v = timeoutReadByte(dev, timeout=600) # using 10min as "inf"
      else:
        v = timeoutReadByte(dev, timeout=inactivity)
      if v == None:
        break
      if printdata:
        print(hex(ord(v)), end=" ")
      seq.append(ord(v))
    if v == None:
      break
    if printdata:
      print("\r")
  return seq

# like scan, but faster and more granular
def packetScan(minimumPacketSize=7, maximumPacketSize=8):
  packet = list(dev.read(minimumPacketSize))

  # if any additional bytes come in within 100ms of each other
  # the are added to the packet, up until the max packet length
  extension = 1
  while extension != None and len(packet) < maximumPacketSize:
    extension = timeoutReadByte(dev, .1)
    if extension != None:
      packet.append(ord(extension))

  return packet 
      

def burstViewer():
  """ utility for understanding ongoing streams of data.
  useful for analog input devices (axes). """

  # my device supplies bursts of 8 bytes per unit
  c = 0
  while True:
    readable = [str(x).zfill(3) for x in dev.read(8)]
    print(readable, end="")

    # captures and discards "overflowing" data
    v = timeoutReadByte(dev, timeout=.1) 
    while v:
      v = timeoutReadByte(dev, timeout=.1) 

    if v == None:
      print (" *** " + str(c).zfill(4))
      c+=1
    else:
      print("-")

def discoverButtonData():
    print("Press something")
    s = scan()
    s2 = scan()
    print(s)
    print(s2)

def similarity(A,T):
  s = 0
  for i in range(min(len(T),len(A))):
    # presume first two bytes are clock
    if A[i] == None or T[i] == None: continue

    s -= abs(A[i] - T[i])

  return s
    
import pyraylib
from pyraylib.colors import *
def byte34map():
  SCREEN_WIDTH, SCREEN_HEIGHT = 500, 500
  window = pyraylib.Window((SCREEN_WIDTH, SCREEN_HEIGHT), 'pyraylib window')
  window.set_fps(60)
  while window.is_open():
      window.begin_drawing()
      window.clear_background(RAYWHITE)

      readable = [x for x in dev.read(8)]

      pyraylib.draw_rectangle(readable[3],10,20,20,YELLOW)
      pyraylib.draw_rectangle(readable[4],40,20,20,PURPLE)
      pyraylib.draw_rectangle(readable[7],70,20,20,BLUE)
      window.end_drawing()

  # Close window and OpenGL context
  window.close()

#######################################################################
#                                                                     # 
#  Step 2: Determine which buttons have which codes...                # 
#                                                                     # 
#######################################################################

# to be added
ids = [
]
# varying signal (ie clock)
V = None

#singleton messages come in 7 bytes
#group messages come in 8 byte bursts

# built in
buttons = [
  ("A Down",               [V, V, 15,   1,   0, 1, 0]),
  ("A Up",                 [V, V, 15,   0,   0, 1, 0]),
  ("B Down",               [V, V, 15,   1,   0, 1, 1]),
  ("B Up",                 [V, V, 15,   0,   0, 1, 1]),
  ("X Down",               [V, V, 15,   1,   0, 1, 2]),
  ("X Up",                 [V, V, 15,   0,   0, 1, 2]),
  ("Y Down",               [V, V, 15,   1,   0, 1, 3]),
  ("Y Up",                 [V, V, 15,   0,   0, 1, 3]),
  ("Start Down",           [V, V, 15,   1,   0, 1, 7]),
  ("Start Up",             [V, V, 15,   0,   0, 1, 7]),
  ("Back Down",            [V, V, 15,   1,   0, 1, 6]),
  ("Back Up",              [V, V, 15,   0,   0, 1, 6]),
  ("DPAD-left Down",       [V, V, 15,   1, 128, 2, 6]),
  ("DPAD-left Up",         [V, V, 15,   0,   0, 2, 6]),
  ("DPAD-right Down",      [V, V, 15, 255, 127, 2, 6]),
  ("DPAD-right Up",        [V, V, 15,   0,   0, 2, 6]),
  ("DPAD-up Down",         [V, V, 15,   1, 128, 2, 7]),
  ("DPAD-up Up",           [V, V, 15,   0,   0, 2, 6]),
  ("DPAD-down Down",       [V, V, 15, 255, 127, 2, 6, V, V, V, 15, 255, 127, 2, 7]),
  ("DPAD-down Up",         [V, V, 15,   0,   0, 2, 6, V, V, V, 15, 255, 127, 2, 6]),
  ("Left bumper Down",      [V, V, 15,   1,   0, 1, 4]),
  ("Left bumper Up",        [V, V, 15,   0,   0, 1, 4]),
  ("Right bumper Down",     [V, V, 15,   1,   0, 1, 5]),
  ("Right bumper Up",       [V, V, 15,   0,   0, 1, 5]),
  ("Home Down",             [V, V, 15,   1,   0, 1, 8]),
  ("Home Up",               [V, V, 15,   0,   0, 1, 8]),
  ("Left toggle Down",      [V, V, 15,   1,   0, 1, 9]),
  ("Left toggle Up",        [V, V, 15,   0,   0, 1, 9]),
  ("Right toggle Down",     [V, V, 15,   1,   0, 1, 10]),
  ("Right toggle Up",       [V, V, 15,   0,   0, 1, 10]),
]

axes = [
 ("Left Trigger Movement", [V, V, 15,   V,   V, 2, 2, V]), 
 ("Left Stick Horiz",      [V, V, 15,   V,   V, 2, 0, V]), 
 ("Left Stick Vert",       [V, V, 15,   V,   V, 2, 1, V]), 
 ("Right Trigger Movement",[V, V, 15,   V,   V, 2, 5, V]), 
 ("Right Stick Horiz",     [V, V, 16,   V,   V, 2, 3, V]), 
 ("Right Stick Vert",      [V, V, 16,   V,   V, 2, 4, V]), 
]

"""
strict message size mode. Replaced with better packetScan solution.

if len(ivalue) == 7:
  sbtns = sorted(buttons, key=lambda a: -similarity(a[1], ivalue))
  # print the name of the best match
  print(sbtns[0][0])
elif len(ivalue) == 15:
  sbtns = sorted(buttons, key=lambda a: -similarity(a[1], ivalue[:7]))
  print(sbtns[0][0].replace("Down", "Tap"))
else:
  print("unexpected message " + str(len(ivalue)) + " bytes long.")

some unused modes. useful for reverse engineering control data layout

#print("Running B34 Map")
#byte34map()

#print("Running Bust Detector...")
#burstViewer()

#if ids:
#  print("Programm mode")
#for name in ids:
#  print(name)
#  value = scan()
#  buttons.append((name, value))
#  print(value)

"""

if __name__ == "__main__":

  device = device or (discoverJoystick()+[None])[0]
  with open(device, "rb") as dev:
    # this step is necessary before the device is usable
    print("Scanning header data")
    scan(inactivity=.01)
    print("Complete")

    print("Test mode")
    while 1:
      ivalue = packetScan()
      sbtns = sorted(buttons+axes, key=lambda a: -similarity(A=a[1], T=ivalue))

      # BTN Down [15] indicates a quick tap
      print(sbtns[0][0] + f" [{len(ivalue)}]", end="")
      if sbtns[0][0] in [axis[0] for axis in axes]:
        print (' value', 128-ivalue[4])
      else:
        print("")
