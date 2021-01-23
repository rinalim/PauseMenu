# Copied from https://github.com/chidea/FBpyGIF/blob/master/FBpyGIF/fb.py

FBIOGET_VSCREENINFO=0x4600
FBIOPUT_VSCREENINFO=0x4601
FBIOGET_FSCREENINFO=0x4602

from mmap import mmap
from fcntl import ioctl
import struct

mm = None
bpp, w, h = 0, 0, 0 # framebuffer bpp and size
bytepp = 0
vx, vy, vw, vh = 0, 0, 0, 0 #virtual window offset and size
vi, fi = None, None
_fb_cmap = 'IIPPPP' # start, len, r, g, b, a
RGB = False
_verbose = False
msize_kb = 0

def report_fb(i=0, layer=0):
  with open('/dev/fb'+str(i), 'r+b')as f:
    vi = ioctl(f, FBIOGET_VSCREENINFO, bytes(160))
    vi = list(struct.unpack('I'*40, vi))
    ffm = 'c'*16+'L'+'I'*4+'H'*3+'ILIIHHH'
    fic = struct.calcsize(ffm)
    fi = struct.unpack(ffm, ioctl(f, FBIOGET_FSCREENINFO, bytes(fic)))

def ready_fb(_bpp=None, i=0, layer=0, _win=None):
  global mm, bpp, w, h, vi, fi, RGB, msize_kb, vx, vy, vw, vh, bytepp
  if mm and bpp == _bpp: return mm, w, h, bpp
  with open('/dev/fb'+str(i), 'r+b')as f:
    vi = ioctl(f, FBIOGET_VSCREENINFO, bytes(160))
    vi = list(struct.unpack('I'*40, vi))
    #(1920, 1080, 1920, 1080, 0, 0, 24, 0,
    #   w     h     vw    vh  xo yo bpp col 
    #            virtual size offset    1=gray
    # 16, 8, 0, 8, 8, 0, 0, 8, 0, 24, 0, 0, 0, 0, 4294967295, 4294967295, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    #   (bit offset, bits, bigend)         non acv   height(mm) width(mm) accl, pixclock, .....                angle, colorspace, reserved[4]
    #     R        G      B      A        std
    bpp = vi[6]
    bytepp = bpp//8
    if _bpp:
      vi[6] = _bpp # 24 bit = BGR 888 mode
      #vi[8] = 0
      #vi[14] = 16
      try:
        vi = ioctl(f, FBIOPUT_VSCREENINFO, struct.pack('I'*40, *vi)) # fb_var_screeninfo
        vi = struct.unpack('I'*40,vi)
        bpp = vi[6]
        bytepp = bpp//8
      except:
        pass
    
    if vi[8] == 0 : RGB = True
    #r_o, r_b, r_e = vi[8:11]
    #g_o, g_b, g_e = vi[11:14]
    #b_o, b_b, b_e = vi[14:17]
    
    ffm = 'c'*16+'L'+'I'*4+'H'*3+'ILIIHHH'
    fic = struct.calcsize(ffm)
    fi = struct.unpack(ffm, ioctl(f, FBIOGET_FSCREENINFO, bytes(fic)))
    #(b'B', b'C', b'M', b'2', b'7', b'0', b'8', b' ', b'F', b'B', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', 
    # 16 char =id
    # 1025519616, 6220800, 0, 0, 2, 1, 1, 0, 5760, 0, 0, 0, 0, 0, 0)
    # smem_len      type type_aux, visual, xpanstep, ypanstep, ywrapstep, line_length, mmio_start, mmio_len, accel, capabilities, reserved[2]
    msize = fi[17] # = w*h*bpp//8
    ll, start = fi[-7:-5]
    # bpp = vi[9]+vi[12]+vi[15]+vi[18]
    w, h = ll//bytepp, vi[1] # when screen is vertical, width becomes wrong. ll//3 is more accurate at such time.
    if _win and len(_win)==4: # virtual window settings
      vx, vy, vw, vh = _win
      if vw == 'w': vw = w
      if vh == 'h': vh = h
      vx, vy, vw, vh = map(int, (vx, vy, vw, vh))
      if vx>=w: vx = 0
      if vy>=h: vy = 0
      if vx>w: vw = w - vx
      else: vw -= vx
      if vy>h: vh = h - vy
      else: vh -= vy
    else:
      vx, vy, vw, vh = 0,0,w,h
    #msize_kb = w*h*bpp//8//1024 # more accurate FB memory size in kb
    msize_kb = vw*vh*bytepp//1024 # more accurate FB memory size in kb
    #xo, yo = vi[4], vi[5]

    mm = mmap(f.fileno(), msize, offset=start)
    return mm, w, h, bpp#ll//(bpp//8), h
def mmseekto(x,y):
  mm.seek((x + y*w) * bytepp)

def numpy_888_565(bt):
  import numpy as np
  arr = np.fromstring(bt, dtype=np.uint32)
  return (((0xF80000 & arr)>>8)|((0xFC00 & arr)>>5)|((0xF8 & arr)>>3)).astype(np.uint16).tostring()

def save_img(img):
  if not type(img) is bytes:
    if not RGB:
      if bpp == 24: # for RPI
        img = img.tobytes('raw', 'BGR')
      else:
        img = img.convert('RGBA').tobytes('raw', 'BGRA')
        if bpp == 16:
          img = numpy_888_565(img)
    else:
      if bpp == 24:
        img = img.tobytes()
      else:
        img = img.convert('RGBA').tobytes()
        if bpp == 16:
          img = numpy_888_565(img)

  f = open('/tmp/fbdump', 'wb')
  f.write(img)
  f.close()

if __name__ == '__main__':
  print('This is a pure Python library file. If you want to use as stand-alone, use \'main.py\' instead.')
  exit(1)
