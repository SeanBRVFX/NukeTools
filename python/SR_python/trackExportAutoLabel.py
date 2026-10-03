'''
Info:
There are countless times when I find myself searching for the source 
of the exported Transform/CornerPin, and when there are many trackers
in the nodegraph, it takes way longer than it should. 
This is a very simple nuke script that appends the Tracker name to the 
exported Transform/CornerPin and adds the Reference Frame to the label knob, 
making it very easy to pinpoint the Tracker.


3) <<ADD TO MENU.PY>>

#### Track Export Auto Label ####
try:
	from trackExportAutoLabel import *
	nuke.addOnUserCreate(trackerExportAutoLabel, nodeClass = "Tracker4")
except: pass

####

'''

def TrackerCallbackStringConstruct():

    CallbackParams = '''

n = nuke.thisNode()
k = nuke.thisKnob()

if k.name() == "createCornerPin":
    try:
        ref_frame = int(tracker["reference_frame"].value())
        try:
            if int(tracker["cornerPinOptions"].getValue()) in (0, 2):
                ref_frame = int(nuke.frame())
        except:
            pass
        transform.setName("%s_%s" % (tracker.name(), transform.name().split("_")[-1]))
        transform["label"].setValue("ref frame: %s" % ref_frame)
        try:
            transform["shutteroffset"].setValue("centred")
        except:
            pass
        del transform
    except:
        pass

    try:
        ref_frame = int(tracker["reference_frame"].value())
        try:
            if int(tracker["cornerPinOptions"].getValue()) in (0, 2):
                ref_frame = int(nuke.frame())
        except:
            pass
        pin.setName("%s_%s" % (tracker.name(), pin.name()))
        pin["label"].setValue("ref frame: %s" % ref_frame)
        try:
            pin["shutteroffset"].setValue("centred")
        except:
            pass
        del pin
    except:
        pass

'''

    return CallbackParams


def trackerExportAutoLabel():
    import nuke
    active_tracker_node = nuke.thisNode()
    active_tracker_node.knob("knobChanged").setValue(TrackerCallbackStringConstruct())