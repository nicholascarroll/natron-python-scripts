from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

def timecode2frame(timecode, fps):
    hours = int(timecode.split(':')[0])
    minutes = int(timecode.split(':')[1])
    seconds = int(timecode.split(':')[2])
    frames = int(timecode.split(':')[3])
    frames += (hours*3600 + minutes*60 + seconds) * fps

    return frames

def frame2timecode(frame, fps):
    seconds = frame/fps
    
    return '{h:02d}:{m:02d}:{s:02d}:{f:02d}'\
        .format(h=int(seconds/3600),
                m=int(seconds/60%60),
                s=int(seconds%60),
                f=int(round(frame%fps)))
