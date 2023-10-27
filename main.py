import image
import time
import display
from AVIParse import *

filename = 'video0_800_480.avi'
avi = AVIParse(filename)
ret = avi.parser_init()

lcd = display.DSIDisplay(
    framesize=display.FWVGA, portrait=True, refresh=60, controller=display.ST7701()
)

clock = time.clock()

while avi.avi_info['cur_img']  <  avi.avi_info['total_frame']:
    clock.tick()

    frame_type = avi.get_frame();
    #print(avi.avi_info['cur_img'], frame_type)

    if frame_type == avi.AVI_VIDEO_FRAME:
        avi.avi_info['cur_img'] += 1
        #print(avi.avi_info)
        img = image.Image(800, 480, image.JPEG, buffer=avi.buf, copy_to_fb=True)
        img.to_rgb565()
        img.replace(transpose=True)
        lcd.write(img)


    print(clock.fps())

print("Done.")
