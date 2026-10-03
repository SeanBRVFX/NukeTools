"""
SR_bakeMetadataFromRead.py
Made by Sean Brian Rowlands

Bake numeric Read / DeepRead metadata to an animated NoOp knob across
the project's frame range.

Installation
    Keep this script with the shared init.py and menu.py in:
        ~/.nuke/plugins/SR_python/
    Add this line once to your user ~/.nuke/init.py:
        nuke.pluginAddPath('./plugins/SR_python')
    Restart Nuke. The folder's menu.py registers the SR_Tools commands.
    Importing this script alone does not register menus or shortcuts.

Usage
    Select a Read / DeepRead, or a node connected downstream from one.
    Choose Nuke menu -> SR_Tools -> Bake Metadata from Read.
    Enter a numeric metadata key (for example exr/focus) and click OK.
    The NoOp provides the baked curve, min/max, invert and divide controls,
    plus an Output knob to reference from other nodes.
    Configure the keyboard shortcut in the shared menu.py.

W_hotbox / Script Editor
    import SR_bakeMetadataFromRead
    SR_bakeMetadataFromRead.bakeMeta()
    Executing this file directly also runs bakeMeta().
"""

import nuke
import tempfile
import os
import re

NODE_BASE_NAME = "SR_bakeMetadata"


def _find_upstream_read(node, max_depth=50):
    visited = set()
    current = node

    for _ in range(max_depth):
        if current is None or id(current) in visited:
            return None

        visited.add(id(current))

        if current.Class() in ("Read", "DeepRead"):
            return current

        if current.inputs() > 0:
            current = current.input(0)
        else:
            return None

    return None


def _sanitize_knob_name(metadata_key):
    name = metadata_key.replace("/", "_").replace("\\", "_")
    name = re.sub(r"[^A-Za-z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")

    if not name or name[0].isdigit():
        name = "val_" + name

    return "baked_{}".format(name)


def bakeMeta():
    sel = nuke.selectedNodes()

    if not sel:
        nuke.message("Select a Read node, or a Dot connected to one.")
        return None

    src = None

    for node in sel:
        if node.Class() in ("Read", "DeepRead"):
            src = node
            break

    if src is None:
        src = _find_upstream_read(sel[0])

    if src is None:
        nuke.message("No Read node found in selection or upstream.")
        return None

    p = nuke.Panel("Bake Metadata To NoOp")
    p.addSingleLineInput("Metadata key", "exr/focus")

    if not p.show():
        return None

    metadata_key = p.value("Metadata key").strip()

    if not metadata_key:
        nuke.message("Metadata key cannot be empty.")
        return None

    dot_main_name = "{}_dot_main".format(NODE_BASE_NAME)
    dot_side_name = "{}_dot_side".format(NODE_BASE_NAME)
    noop_name = "{}_node".format(NODE_BASE_NAME)
    knob_name = _sanitize_knob_name(metadata_key)

    nk_lines = [
        "set cut_paste_input [stack 0]",
        "version 15.1 v6",
        "push $cut_paste_input",
        "Dot {",
        " name " + dot_main_name,
        " selected true",
        " xpos 0",
        " ypos 0",
        "}",
        "Dot {",
        " name " + dot_side_name,
        " selected true",
        " xpos 0",
        " ypos 0",
        "}",
        "NoOp {",
        " name " + noop_name,
        " selected true",
        " xpos 0",
        " ypos 0",
        " addUserKnob {20 User}",
        " addUserKnob {7 " + knob_name + " l " + knob_name + "}",
        " " + knob_name + " 0",
        " addUserKnob {26 sep1 l {}}",
        " addUserKnob {6 flip_curve l {Invert/Flip} +STARTLINE}",
        " addUserKnob {7 curve_min l Min R 0 100}",
        " addUserKnob {7 curve_max l Max R 0 100}",
        " addUserKnob {7 divide_by l {Divide by} R 1 1000}",
        " divide_by 100",
        " addUserKnob {26 sep2 l {}}",
        " addUserKnob {7 output l {<b>Output</b>} R 0 100}",
        "}",
    ]

    nk_text = "\n".join(nk_lines)

    tmp_path = None
    created_nodes = []

    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".nk")
        os.close(fd)

        with open(tmp_path, "w") as f:
            f.write(nk_text)

        for n in nuke.allNodes():
            n.setSelected(False)

        nuke.nodePaste(tmp_path)
        pasted = nuke.selectedNodes()
        created_nodes = list(pasted)

        if len(pasted) < 3:
            nuke.message("Failed to create metadata bake branch.")
            return None

        dot_main = None
        dot_side = None
        dst = None

        for n in pasted:
            if n.Class() == "Dot" and n.name().startswith(dot_main_name):
                dot_main = n
            elif n.Class() == "Dot" and n.name().startswith(dot_side_name):
                dot_side = n
            elif n.Class() == "NoOp" and n.name().startswith(noop_name):
                dst = n

        if dot_main is None or dot_side is None or dst is None:
            nuke.message("Could not identify pasted nodes.")
            return None

        main_x = src.xpos() + 34
        main_y = src.ypos() + 160

        side_x = main_x + 130
        side_y = main_y

        noop_x = side_x - 34
        noop_y = side_y + 33

        dot_main.setXpos(main_x)
        dot_main.setYpos(main_y)

        dot_side.setXpos(side_x)
        dot_side.setYpos(side_y)

        dst.setXpos(noop_x)
        dst.setYpos(noop_y)

        dot_main.setInput(0, src)
        dot_side.setInput(0, dot_main)
        dst.setInput(0, dot_side)

        dst["label"].setValue("baked: {}".format(metadata_key))

        baked_knob = dst[knob_name]
        baked_knob.setAnimated()

        first = int(nuke.root().firstFrame())
        last = int(nuke.root().lastFrame())
        total = max(1, last - first + 1)

        task = nuke.ProgressTask("Baking metadata")
        task.setMessage("Starting...")

        baked_min = None
        baked_max = None

        for i, frame in enumerate(range(first, last + 1), 1):
            if task.isCancelled():
                for node in created_nodes:
                    try:
                        nuke.delete(node)
                    except Exception:
                        pass

                return None

            percent = int((float(i) / float(total)) * 100.0)
            task.setProgress(percent)
            task.setMessage("Key: {} | Frame {} of {}".format(metadata_key, frame, last))

            try:
                value = src.metadata(metadata_key, frame)

                if value is None or value == "":
                    continue

                fval = float(value)
                baked_knob.setValueAt(fval, frame)

                if baked_min is None or fval < baked_min:
                    baked_min = fval
                if baked_max is None or fval > baked_max:
                    baked_max = fval

            except Exception:
                pass

        # Set min/max and output expression
        if baked_min is not None:
            dst["curve_min"].setValue(baked_min)
            dst["curve_max"].setValue(baked_max)

        dst["output"].setExpression(
            "(flip_curve ? (curve_min + curve_max - {0}) : {0}) / divide_by".format(knob_name)
        )

        task.setProgress(100)
        task.setMessage("Done")

        return dst

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


if __name__ == "__main__":
    bakeMeta()
