from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from NatronGui import *


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

def create_timeread(): 
    """Makes the read node use timecodes instead of frame numbers.
    """
    # VALIDATION
    selectedNodes = app1.getSelectedNodes()
    if len(selectedNodes) != 1: 
        natron.informationDialog("Info","Select one reader.")
        return
    reader = selectedNodes[0]
    if reader.getPluginID() not in natron.getPluginIDs('.Read'):
        natron.informationDialog("Info","First select a reader.")
        return
        
    # Create the user parameters
    reader.userNatron = reader.createPageParam("userNatron", "Timecodes")
    in_timecode = reader.createStringParam("InTimecode", "In Timecode")
    out_timecode = reader.createStringParam("OutTimecode", "Out Timecode")
    reader.userNatron.addParam(in_timecode)
    reader.userNatron.addParam(out_timecode)

    first_frame = reader.getParam('firstFrame')
    last_frame = reader.getParam('lastFrame')
    frame_rate = reader.getParam('frameRate')

    in_timecode.setValue(frame2timecode(first_frame.getValue(),frame_rate.getValue()))
    out_timecode.setValue(frame2timecode(last_frame.getValue(),frame_rate.getValue()))
    first_frame.setExpression("timecode2frame(thisNode.getParam('InTimecode').getValue(),thisNode.getParam('frameRate').getValue())", False, 0)
    last_frame.setExpression("timecode2frame(thisNode.getParam('OutTimecode').getValue(),thisNode.getParam('frameRate').getValue())", False, 0)
    reader.refreshUserParamsGUI()


NatronGui.natron.addMenuCommand('Custom/Use Timecodes for Reader','create_timeread')
