import nuke
import os
import subprocess

def open_selected_node_in_explorer():
    node = nuke.selectedNode()
    
    if node.Class() not in ["Read", "Write"]:
        nuke.message("Please select a Read or Write node.")
        return

    file_path = nuke.filename(node)
    if not file_path:
        nuke.message("Could not find a valid file path on the selected node.")
        return

    folder_path = os.path.dirname(file_path)

    if not os.path.exists(folder_path):
        nuke.message("Folder does not exist:\n{}".format(folder_path))
        return

    subprocess.Popen(r'explorer "{}"'.format(os.path.normpath(folder_path)))
