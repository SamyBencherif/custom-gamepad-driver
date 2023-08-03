import usb
import time

"""
Thanks to https://www.partsnotincluded.com/understanding-the-xbox-360-wired-controllers-usb-data/
"""

def uint16(i):
  return i-0x10000 if i>>0xf else i

class Gamepad:

  def __init__(self):
    self._device = usb.core.find(idVendor=0x045e, idProduct=0x028e)
    if self._device is None:
      print("Waiting for gamepad...")
      while self.device is None:
        self._device = usb.core.find(idVendor=0x045e, idProduct=0x028e)
        time.sleep(.1)
    self._device.set_configuration()
    self._prevdata = None
    # TODO dispatch own update loop on another thread?

  def rumble(self, left=255, right=None):
    if right is None: right = left
    raise NotImplementedError()
    # [0x00, 0x08, 0x00, left, right, 0x00, 0x00, 0x00])

  def led(self, anim=0x00):
    """
    0x00	 All off
    0x01	 All blinking
    0x02	 1 flashes, then on
    0x03	 2 flashes, then on
    0x04	 3 flashes, then on
    0x05	 4 flashes, then on
    0x06	 1 on
    0x07	 2 on
    0x08	 3 on
    0x09	 4 on
    0x0A	 Rotating (e.g. 1-2-4-3)
    0x0B	 Blinking*
    0x0C	 Slow blinking*
    0x0D	 Alternating (e.g. 1+4-2+3), then back to previous*
    """
    raise NotImplementedError()
    #[0x01, 0x03, anim]

  def update(self):
    d = self._device.read(0x81, 20)

    # ignore messages I don't understand
    if d[0] != 0 or d[1] != 20:
      return
    
    self._data = d

    if self._prevdata is None:
      self._prevdata = self._data

    self._prevdata = self._data

  def __getattr__(self, btn):

    if btn.startswith('_'): src = self._prevdata
    else: src = self._data

    if btn == "a": return (src[3]>>4)&1
    if btn == "b": return (src[3]>>5)&1 
    if btn == "x": return (src[3]>>6)&1
    if btn == "y": return (src[3]>>7)&1

    if btn == "d_left": return (src[2]>>2)&1
    if btn == "d_right": return (src[2]>>3)&1
    if btn == "d_up": return (src[2]>>0)&1
    if btn == "d_down": return (src[2]>>1)&1

    if btn == "back": return (src[2]>>5)&1
    if btn == "start": return (src[2]>>4)&1

    if btn == "lb": return (src[3]>>0)&1
    if btn == "rb": return (src[3]>>1)&1

    if btn == "ls": return (src[2]>>6)&1
    if btn == "rs": return (src[2]>>7)&1

    if btn == "ljoy_sx": return uint16(src[6]+(src[7]<<8))/0x7fff
    if btn == "ljoy_sy": return uint16(src[8]+(src[9]<<8))/0x7fff

    """
    self.ljoy_x = self.ljoy_sx
    self.ljoy_y = self.ljoy_sy
    m = (self.ljoy_x**2 + self.ljoy_y**2) ** .5
    if m > 1:
      self.ljoy_x /= m
      self.ljoy_y /= m
    """

    if btn == "rjoy_sx": return uint16(src[10]+(src[11]<<8))/0x7fff
    if btn == "rjoy_sy": return uint16(src[12]+(src[13]<<8))/0x7fff

    if btn == "lt": return src[4]/0xff
    if btn == "rt": return src[5]/0xff

  def pretty(self):
    A = '[A]' if self.a else ' A '
    B = '[B]' if self.b else ' B '
    X = '[X]' if self.x else ' X '
    Y = '[Y]' if self.y else ' Y '

    l = '[<]' if self.d_left else ' < '
    r = '[>]' if self.d_right else ' > '
    u = '[^]' if self.d_up else ' ^ '
    d = '[v]' if self.d_down else ' v '

    e = '[<]' if self.back else ' < '
    s = '[>]' if self.start else ' > '

    lb = '[###]' if self.lb else '[   ]'
    rb = '[###]' if self.rb else '[   ]'

    L = [[' ' for i in range(3)] for j in range(3)]
    L[1+round(self.ljoy_sy)][1+round(self.ljoy_sx)] = '*' if self.ls else 'o'
    L = [''.join(row) for row in L]

    R = [[' ' for i in range(3)] for j in range(3)]
    R[1+round(self.rjoy_sy)][1+round(self.rjoy_sx)] = '*' if self.rs else 'o'
    R = [''.join(row) for row in R]

    lt0 = ['   ', ' # ', '###'][min(2, round(self.lt*2/.75))]
    lt1 = [' ', '#'][self.lt > .75]

    rt0 = ['   ', ' # ', '###'][min(2, round(self.rt*2/.75))]
    rt1 = [' ', '#'][self.rt > .75]
   
    return f"""
         |{lt1}|                        |{rt1}| 
        |{lt0}|                      |{rt0}|
        ------_____________________------
      / { lb}                       { rb} $
       -----------------------------------
      |  /{L[2]}$                     {Y}     $      
     /   |{L[1]}|   {e} #### {s}   {X}   {B}   |     
    /    ${L[0]}/                     {A}      $     
    |                       ___              $    
   /         {u}           /{R[2]}$             |   
  /       {l}   {r}        |{R[1]}|             $   
 /           {d}           ${R[0]}/             $
 |         /-------------------------$        $  
 |        /-                          $-       | 
 /       /                             $        $ 
 -     /-                                $-      |
  $-  -                                    $-  /- 
    $-                                       $-   
""".replace("$", "\\")

import pyautogui
pyautogui.FAILSAFE = False

g = Gamepad()
try:
  while True:
    g.update()
    print(U"\u001b[H\r" + g.pretty())
    time.sleep(50/1000)

    # drive the mouse
    mouse_speed = 20
    pyautogui.move(mouse_speed*g.ljoy_sx, -mouse_speed*g.ljoy_sy)

except KeyboardInterrupt:
  pass
