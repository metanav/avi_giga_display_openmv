import image
import time
import display
from AVIParse import *

filename = 'video.avi'
avi = AVIParse(filename)
ret = avi.parser_init()

lcd = display.DSIDisplay(
    framesize=display.FWVGA, portrait=True, refresh=60, controller=display.ST7701()
)

clock = time.clock()
t = time.ticks_us()

while True:
    while avi.avi_info['cur_img'] < avi.avi_info['total_frame']:
        clock.tick()
        
        frame_type = avi.get_frame()
        if frame_type == avi.AVI_VIDEO_FRAME:
            avi.avi_info['cur_img'] += 1
           
            img = image.Image(avi.avi_info['width'], avi.avi_info['height'],
                              image.JPEG, buffer=avi.buf, copy_to_fb=True)
            lcd.write(img, hint=image.CENTER|image.ROTATE_90)

            while time.ticks_diff(time.ticks_us(), t) < avi.avi_info['sec_per_frame']:
                pass
            t = time.ticks_add(t, avi.avi_info['sec_per_frame'])

        print(clock.fps())

    avi.avi_info['cur_img'] = 0
