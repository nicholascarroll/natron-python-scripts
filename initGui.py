# http://github.com/nicholascarroll/natron-python-scripts/initGui.py

# TODO ADD SHOT LIST
# This is a workaround for https://github.com/MrKepzie/Natron/issues/1403

# Capabilities:
# - import a video track from a AAF file into a list of shots
# - sort the list by media file name
# - create/open Natron project files 
# - export the list to a new track in the same AAF file

# The first field is the AAF filename and that gets read in.

# This will be a sortable table. Each row being one shot with one reader and one writer.
# A shot is a single frame range from a single source media file

# The columns will be:
# - Timecode (the timecode on the AAF timeline)
# - Offset (the frame number of the In frame on the AAF timeline)
# - In (the starting frame number)
# - Out (the ending frame number)
# - Read File (this needs to be the full path, but just show the last n chars)
# - Read Node (scriptname)
# - Write File (this needs to be the full path, but just show the last n chars)
# - Write Node (scriptname)
# - Natron Project Filename
# - Notes (free text entry)

# All this data has to be kept somewhere and maybe the best is to keep it in the AAF

# and then a button to write all this back to the AAF. This is an update button
# because you can jusk keep pressing it and overwriting the AAF.

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
#(install Pyaaf from: http://markreidvfx.github.io/pyaaf)
import aaf
import aaf.component
import operator
from PySide.QtGui import *
from PySide.QtCore import *
#To import the variable "natron":
from NatronGui import *


def get_video_tracks(mob):
    tracks = []
    
    for slot in mob.slots():

        if slot.media_kind == "DataDef_Picture": 
            segment = slot.segment
            
            if isinstance(segment, aaf.component.NestedScope):               
                for nested_segment in segment.segments():                   
                    if isinstance(nested_segment,  aaf.component.Sequence):
                        tracks.append(list(nested_segment.components()))
                        
            elif isinstance(segment, aaf.component.Sequence):
                tracks.append(list(segment.components()))
                
            elif isinstance(segment, aaf.component.SourceClip):
                tracks.append([segment])

    return tracks

def load_data(aaf_filename):
    f = aaf.open(aaf_filename, "r")

    # get the main composition
    main_composition = f.storage.toplevel_mobs()[0]

    # print the name of the composition.
    print (main_composition.name)

    # AAFObjects have properties that can be accessed like a dictionary
    # print out the creation time
    print (main_composition['CreationTime'].value)

    video_tracks = get_video_tracks(main_composition)

    for source_clip in video_tracks[0]:
        print (source_clip['SourceID'].value)
        print (source_clip.slot_id)
        # slotID - the track identifier, is valuable because it means we can just deal with clips. 

#The Shotlist panel
class Shotlist(NatronGui.PyPanel):
    #Register a custom signal
    userFileChanged = QtCore.Signal()

    #Slots should be decorated:
    #http://qt-project.org/wiki/Signals_and_Slots_in_PySide
    
    #This is called upon a user click on the button
    @QtCore.Slot()
    def onButtonClicked(self):
        location = self.currentApp.getFilenameDialog(("aaf"))
        if location:
            self.locationEdit.setText(location)

            #Save the file
            self.onUserDataChanged()
            
        self.userFileChanged.emit()

    #This is called when the user finish editing of the line edit
    @QtCore.Slot()
    def onLocationEditEditingFinished(self):
        #Save the file
        self.onUserDataChanged()
        self.userFileChanged.emit()
            
    #This is called when our custom userFileChanged signal is emitted
    @QtCore.Slot()
    def onFileChanged(self):
        print("onfilechanged")

    def __init__(self,scriptName,label,app):

        #Init base class, important! otherwise signals/slots won't work.
        NatronGui.PyPanel.__init__(self,scriptName, label, False, app)

        #Store the current app as it might no longer be pointing to the app at the time being called #when a slot will be invoked later on
        self.currentApp = app

        #Set the layout
        self.setLayout( QVBoxLayout())

        #Create a widget container for the line edit + button
        fileContainer = QWidget(self)
        fileLayout = QHBoxLayout()
        fileContainer.setLayout(fileLayout)

        #Create the line edit, make it expand horizontally
        self.locationEdit = QLineEdit(fileContainer)
        self.locationEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        #Create a pushbutton
        self.button = QPushButton(fileContainer)
        #Decorate it with the open-file pixmap built-in into Natron
        #buttonPixmap = natron.getIcon(NatronEngine.Natron.PixmapEnum.NATRON_PIXMAP_OPEN_FILE)
        #self.button.setIcon(QIcon(buttonPixmap))

        #Add widgets to the layout
        fileLayout.addWidget(self.locationEdit)
        fileLayout.addWidget(self.button)

        # Make a table
        table_model = Table(self, data_list, header)
        table_view = QTableView()
        table_view.setModel(table_model)
        # set font
        font = QFont("Courier New", 14)
        table_view.setFont(font)
        # set column width to fit contents (set font first!)
        table_view.resizeColumnsToContents()
        # enable sorting
        table_view.setSortingEnabled(True)

        #Add widgets to the layout
        self.layout().addWidget(fileContainer)
        self.layout().addWidget(table_view)

        load_data("/Users/nick/White-Tipped-Shark_m4v (Edit).aaf")


        #Make signal/slot connections
        self.button.clicked.connect(self.onButtonClicked)
        self.locationEdit.editingFinished.connect(self.onLocationEditEditingFinished)
        self.userFileChanged.connect(self.onFileChanged)

    # We override the save() function and save the filename
    def save(self):
        return self.locationEdit.text()

    # We override the restore(data) function and restore the current image
    #def restore(self,data):
    #    self.locationEdit.setText(data)
    #    self.label.setPixmap(QPixmap(data))

class Table(QAbstractTableModel):
    def __init__(self, parent, mylist, header, *args):
        QAbstractTableModel.__init__(self, parent, *args)
        self.mylist = mylist
        self.header = header
    def rowCount(self, parent):
        return len(self.mylist)
    def columnCount(self, parent):
        return len(self.mylist[0])
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None
        return self.mylist[index.row()][index.column()]
    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None
    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.mylist = sorted(self.mylist,
            key=operator.itemgetter(col))
        if order == Qt.DescendingOrder:
            self.mylist.reverse()
        self.emit(SIGNAL("layoutChanged()"))

# dummy data for prototype
header = ['Timecode', ' Offset', ' In', ' Out',  ' Read File', ' Read Node',  ' Write File', ' Write Node',
          ' Natron Project Filename', 'Notes']

data_list = [
('00:01:25+09', 2040, 200, 247,  '/vids/projectx/1_0062.####.dng'),
('00:01:27+09', 2047, 1102, 1151, '/vids/projectx/1_0063.####.dng'),
('00:01:34+10', 2266, 500, 693, '/vids/projectx/1_0062.####.dng')
]
#To be called to create a new icon viewer panel:
#Note that *app* should be defined. Generally when called from onProjectCreatedCallback
#this is set, but when called from the Script Editor you should set it yourself beforehand:
#app = app1
#See http://natron.readthedocs.org/en/python/natronobjects.html for more info
def createShotlist():
    if hasattr(app,"p"):
        #The icon viewer already exists, it we override the app.p variable, then it will destroy the
        #and create a new one but we don't really need it

        #The warning will be displayed in the Script Editor
        print("Note for us developers: this widget already exists!")
        return

    #Create our shotlist
    app.p = Shotlist("com.casanico.shotlist","Shotlist",app)

    #Add it to the "pane2" tab widget
    app.pane2.appendTab(app.p);

    
    #Register the tab to the application, so it is saved into the layout of the project
    #and can appear in the Panes sub-menu of the "Manage layout" button 
    app.registerPythonPanel(app.p,"createShotlist")
    #Callback set in the "After project created" parameter in the Preferences-->Python tab of Natron
    #This will automatically create our panels when a new project is created
    def onProjectCreatedCallback(app):
        #Always create our icon viewer on project creation, you must register this call-back in the
        #"After project created callback" parameter of the Preferences-->Python tab.
        createShotlist()

#Add a custom menu entry with a shortcut to create our icon viewer
NatronGui.natron.addMenuCommand('Custom/Shotlist','createShotlist')
