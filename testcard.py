from PIL import Image, ImageDraw

import numpy as np

BG = (255, 255, 255)
FG = (0, 0, 0)

SIZE = 640
BORDER=4
DIVS=20
WIDTH=SIZE/DIVS

im = Image.new('RGBA', (SIZE, SIZE), BG)

draw = ImageDraw.Draw(im)
extent = SIZE+2*BORDER
for x in np.linspace(0, extent, DIVS):
    c = int(255*x/extent)
    draw.rectangle((x, 0, x+WIDTH-BORDER, SIZE), fill=(c, c, c))

im.save("testcard.png")

