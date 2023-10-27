import io
import struct

class AVIStatus:
    AVI_OK         = 0
    AVI_RIFF_ERR   = 1
    AVI_AVI_ERR    = 2
    AVI_LIST_ERR   = 3
    AVI_HDRL_ERR   = 4
    AVI_AVIH_ERR   = 5
    AVI_STRL_ERR   = 6
    AVI_STRH_ERR   = 7
    AVI_STRF_ERR   = 8
    AVI_MOVI_ERR   = 9
    AVI_FORMAT_ERR = 10
    AVI_STREAM_ERR = 11

class AVIParse:
    AVI_VIDS_FLAG = 0x6463
    AVI_AUDS_FLAG = 0x7762
    AVI_VIDEO_FRAME = 1
    AVI_AUDIO_FRAME = 2

    def __init__(self, filename):
        self.f = io.open(filename, 'rb')

        self.f.seek(0, 2)

        self.avi_info = {}
        self.avi_info['file_size'] = self.f.tell()
        self.avi_info['cur_img'] = 0

        self.f.seek(0, 0)
        self.a_buf = None

        self.buf = self.f.read(96 * 1024)
        if len(self.buf) != 96 * 1024:
            print("Failed")

    def avi_search_id(self, offset, id):
        id = bytes(id, 'ascii')

        for i in range(len(self.buf) - 4 + offset):
            if self.buf[i] == id[0] and self.buf[i+1] == id[1] and self.buf[i+2] == id[2] and self.buf[i+3] == id[3]:
                return i

        return 0

    def avi_get_stream_info(self, offset):
        stream_id,   = struct.unpack('>H', self.buf[offset+2:offset+4])
        stream_size, = struct.unpack('<L', self.buf[offset+4:offset+8])
        #print(offset, stream_id, stream_size)

        self.avi_info['stream_id'] = stream_id
        self.avi_info['stream_size'] = stream_size

        if self.avi_info['stream_size'] % 2:
            self.avi_info['stream_size'] += 1


        if (self.avi_info['stream_id']  ==  self.AVI_VIDS_FLAG) or (self.avi_info['stream_id']  ==  self.AVI_AUDS_FLAG):
            return AVIStatus.AVI_OK;

        return AVIStatus.AVI_STREAM_ERR;

    def get_frame(self):
        if self.avi_info['cur_img'] == 0:
            self.f.seek(0, 0) # Go to the file start
            self.buf = self.f.read(72*1024)

            offset = self.avi_search_id(0, 'movi');
            # Read first frame info
            self.avi_get_stream_info(offset+4)
            # Go to the first frame offset in the avi file
            self.f.seek(offset + 12, 0)

        # Get the current frame size
        self.avi_info['frame_size'] = self.avi_info['stream_size']

        if self.avi_info['stream_id']  ==  self.AVI_VIDS_FLAG:
            # Read The current frame + the header of the next frame (8 bytes)

            self.buf = self.f.read(self.avi_info['frame_size'] + 8)
            # Get the info of the next frame
            self.avi_get_stream_info(self.avi_info['stream_size'])
            return self.AVI_VIDEO_FRAME

        if self.avi_info['stream_id']  ==  self.AVI_AUDS_FLAG:
            # Read The current frame + the header of the next frame (8 bytes)
            self.buf = self.f.read(self.avi_info['frame_size'] + 8)

            # Get the info of the next frame
            self.avi_get_stream_info(self.avi_info['stream_size'])
            return self.AVI_AUDIO_FRAME

        return 0

    def parser_init(self):
        start = 0
        end = 3 * 4
        data = self.buf[start:end]
        riff_id, file_size, avi_id =  struct.unpack('<4sL4s', data)

        if riff_id != b'RIFF':
            return AVIStatus.AVI_RIFF_ERR

        if avi_id != b'AVI ':
            return AVIStatus.AVI_AVI_ERR

        start += len(data)
        end   = start + 3 * 4
        data = self.buf[start:end]
        list_id, block_size, list_type =  struct.unpack('<4sL4s', data)

        if list_id != b'LIST':
            return AVIStatus.AVI_LIST_ERR

        if list_type != b'hdrl':
            return AVIStatus.AVI_HDRL_ERR

        start += len(data)
        end   = start + 16 * 4
        data = self.buf[start:end]
        block_id, block_size, sec_per_frame, _, _, _, total_frame, *_  =  struct.unpack('<4s15L', data)

        if block_id != b'avih':
            return AVIStatus.AVI_AVIH_ERR

        self.avi_info['sec_per_frame'] = sec_per_frame
        self.avi_info['total_frame']   = total_frame

        start += block_size + 8
        end   = start + 3 * 4
        data  = self.buf[start:end]
        list_id, block_size, list_type =  struct.unpack('<4sL4s', data)

        if list_id != b'LIST':
            return AVIStatus.AVI_LIST_ERR

        if list_type != b'strl':
            return AVIStatus.AVI_STRL_ERR
        lh_start = start
        lh_block_size = block_size

        start += 12
        end   = start + 64
        data = self.buf[start:end]
        block_id, block_size, stream_type, handler, *_ =  struct.unpack('<4sL4s4sL2H8L4H', data)

        if block_id != b'strh':
            return AVIStatus.AVI_STRH_ERR

        if stream_type == b'vids':
            if handler != b'MJPG':
                return AVIStatus.AVI_FORMAT_ERR;

            self.avi_info['video_flag'] = '00dc'
            self.avi_info['audio_flag'] = '01wb'

            start += 64 #12 + block_size + 8
            end   = start + 13 * 4
            data = self.buf[start:end]
            block_id, _, _, width, height, *_ =  struct.unpack('<4s12L', data)

            if block_id != b'strf':
                return AVIStatus.AVI_STRF_ERR

            self.avi_info['width']  = width
            self.avi_info['height'] = height

            start = lh_start + lh_block_size + 8
            end   = start + 3 * 4
            data = self.buf[start:end]
            list_id, block_size, list_type =  struct.unpack('<4sL4s', data)

            if list_id != b'LIST':
                self.avi_info['sample_rate'] = 0
                self.avi_info['channels']    = 0
                self.avi_info['audio_type']  = 0
            else:
                if list_type != b'strl':
                    return AVIStatus.AVI_STRL_ERR

                start += 12
                end   = start + 64
                data = self.buf[start:end]
                block_id, block_size, stream_type, *_ =  struct.unpack('<4sL4s13L', data)

                if block_id != b'strh':
                    return AVIStatus.AVI_STRH_ERR

                if stream_type != b'auds':
                    return AVIStatus.AVI_FORMAT_ERR

                start += block_size + 8
                end   = start + 24
                data = self.buf[start:end]
                block_id, block_size, format_tag, channels, sample_rate, *_ =  struct.unpack('<4sLHHLLHH', data)

                if block_id != b'strf':
                    return AVIStatus.AVI_STRF_ERR

                self. avi_info['sample_rate'] = sample_rate
                self.avi_info['channels']    = channels
                self.avi_info['audio_type']  = format_tag

            offset = self.avi_search_id(0, 'movi')
            if offset == 0:
                return AVIStatus.AVI_MOVI_ERR

            if self.avi_info['sample_rate'] > 0:
                start += offset
                offset = self.avi_search_id(start, self.avi_info['audio_flag'])
                if offset == 0:
                    return AVIStatus.AVI_STREAM_ERR

                start += offset + 4
                end   = start + 2
                data = self.buf[start:end]
                audio_buf_size, = struct.unpack('<H', data)
                self.avi_info['audio_buf_size'] = audio_buf_size

        return AVIStatus.AVI_OK


