"""
SR_HSVLfromROI.py
─────────────────────────────────────────────────────────────────────────────
Sample the average colour from the active Viewer's ROI (colour-sample bbox),
convert it to HSVL (Hue / HSV-Saturation / HSV-Value / BT.709 Luminance),
and drop a StickyNote in the node graph.

Usage
    • Ctrl + Shift + Enter      : Quick Sample HSVL (Instant StickyNote)
    • Ctrl + Shift + Alt + Enter: Sample HSVL with Options (Dialog for Label & Constant)
    • Menu : Viewer right-click → HSVL Sampler

    If no ROI has been drawn in the Viewer the command silently does nothing.

Registration example
    ~/.nuke/init.py   →  nuke.pluginAddPath('./python/SR_HSVLfromROI/')
    ~/.nuke/menu.py   →  import SR_HSVLfromROI

─────────────────────────────────────────────────────────────────────────────
"""

import math
import nuke


# ─── Colour math ─────────────────────────────────────────────────────────────

def _rgb_to_hsvl(r, g, b):
    """Return (H°, S, V, L) from linear-float r, g, b.

    H  – hue in degrees  [0 – 360)
    S  – HSV saturation  [0 – 1]
    V  – HSV value       [0 – 1]   (= max(r,g,b))
    L  – luminance       (BT.709 weighted linear, unlimited range)
    """
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    delta = max_c - min_c

    # Value
    V = max_c

    # Luminance (BT.709)
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # Saturation
    S = (delta / max_c) if max_c != 0 else 0.0

    # Hue
    if delta == 0:
        H = 0.0
    elif max_c == r:
        H = (60.0 * ((g - b) / delta) + 360.0) % 360.0
    elif max_c == g:
        H = (60.0 * ((b - r) / delta) + 120.0) % 360.0
    else:
        H = (60.0 * ((r - g) / delta) + 240.0) % 360.0

    return H, S, V, L


def _get_viewer_scale(viewer_node):
    """Calculate the total display scale factor applied to the node graph by Viewer."""
    try:
        downrez_val = int(viewer_node["downrez"].value())
        downrez_scale = 1.0 / max(1, downrez_val)
    except Exception:
        downrez_scale = 1.0

    root = nuke.root()
    if root["proxy"].value():
        try:
            if root["proxy_type"].value() == "scale":
                proxy_scale = float(root["proxy_scale"].value())
            else:
                pf = root["proxy_format"].value()
                rf = root["format"].value()
                proxy_scale = float(pf.width()) / float(rf.width())
        except Exception:
            proxy_scale = 0.5
    else:
        proxy_scale = 1.0

    return proxy_scale * downrez_scale


def _sample_roi_rgb():
    """Sample the ROI and return (r, g, b, px1, py1, px2, py2, viewer_node) or None."""

    viewer = nuke.activeViewer()
    if viewer is None:
        nuke.message("No active Viewer found.")
        return None

    viewer_node = viewer.node()

    active_idx = viewer.activeInput()
    if active_idx is None:
        active_idx = 0

    upstream = viewer_node.input(active_idx)
    if upstream is None:
        nuke.message("The active Viewer has no connected input to sample from.")
        return None

    bbox = viewer_node["colour_sample_bbox"].value()

    if bbox[0] == bbox[2] or bbox[1] == bbox[3]:
        return None

    w = float(upstream.width())
    h = float(upstream.height())
    aspect = (w * float(upstream.pixelAspect())) / h

    x1 = (bbox[0] * 0.5 + 0.5) * w
    y1 = (((bbox[1] * 0.5) + (0.5 / aspect)) * aspect) * h
    x2 = (bbox[2] * 0.5 + 0.5) * w
    y2 = (((bbox[3] * 0.5) + (0.5 / aspect)) * aspect) * h

    px1 = int(round(min(x1, x2)))
    px2 = int(round(max(x1, x2)))
    py1 = int(round(min(y1, y2)))
    py2 = int(round(max(y1, y2)))

    if px2 <= px1 or py2 <= py1:
        return None

    # Full-resolution center and dimensions
    cx = (px1 + px2) * 0.5
    cy = (py1 + py2) * 0.5
    dx = float(px2 - px1)
    dy = float(py2 - py1)

    # Scale to active processing resolution if in Downrez or Proxy mode
    scale = _get_viewer_scale(viewer_node)
    cx_s = cx * scale
    cy_s = cy * scale
    dx_s = max(1.0, dx * scale)
    dy_s = max(1.0, dy * scale)

    try:
        r = upstream.sample("red",   cx_s, cy_s, dx_s, dy_s)
        g = upstream.sample("green", cx_s, cy_s, dx_s, dy_s)
        b = upstream.sample("blue",  cx_s, cy_s, dx_s, dy_s)
    except Exception as e:
        nuke.message("Could not sample the image:\n%s" % str(e))
        return None

    return (r, g, b, px1, py1, px2, py2, viewer_node)


def _create_hsvl_sticky(r, g, b, px1, py1, px2, py2, viewer_node, title=None, create_constant=False):
    """Build the HSVL StickyNote (and optional Constant node) from sampled RGB values."""

    H, S, V, L_raw = _rgb_to_hsvl(r, g, b)

    H_str = "%.0f" % H
    S_str = "%.2f" % S
    V_str = "%.2f" % V
    L_str = "%.5f" % L_raw

    frame = nuke.frame()
    if title:
        header = "<b>HSVL at frame {frame} ({title})</b>".format(frame=frame, title=title)
    else:
        header = "<b>HSVL at frame {frame}</b>".format(frame=frame)

    label = (
        "{header}\n"
        "H  {h}\n"
        "S  {s}\n"
        "V  {v}\n"
        "L  {l}\n"
        "<small>\n"
        "R {r:.5f}  \n"
        "G {g:.5f}  \n"
        "B {b:.5f}\n"
        "</small><small><small>x={px1} y={py1} {rw}x{rh}</small></small>"
    ).format(header=header, h=H_str, s=S_str, v=V_str, l=L_str,
             r=r, g=g, b=b, px1=px1, py1=py1,
             rw=px2 - px1, rh=py2 - py1)

    sticky = nuke.createNode("StickyNote", inpanel=False)
    sticky["label"].setValue(label)
    sticky["tile_color"].setValue(0x555555ff)
    sticky["note_font"].setValue("Arial Black")
    sticky["note_font_size"].setValue(14)

    if create_constant:
        const_node = nuke.createNode("Constant", inpanel=False)
        const_node["color"].setValue([r, g, b, 1.0])

        active_idx = nuke.activeViewer().activeInput() if nuke.activeViewer() else 0
        upstream = viewer_node.input(active_idx or 0)
        if upstream and hasattr(upstream, "format") and upstream.format():
            try:
                const_node["format"].setValue(upstream.format().name())
            except Exception:
                pass

        if title:
            const_node["label"].setValue("HSVL: %s\nFrame %s" % (title, frame))
        else:
            const_node["label"].setValue("HSVL Sample\nFrame %s" % frame)

        # Place Constant neatly to the right of the StickyNote
        offset_x = max(180, sticky.screenWidth() + 30)
        const_node.setXYpos(sticky.xpos() + offset_x, sticky.ypos())


_last_create_constant = False


def sample_hsvl_to_sticky(ask_options=True):
    """Sample the ROI and create an HSVL StickyNote with options dialog (Ctrl+Shift+Enter)."""
    global _last_create_constant

    result = _sample_roi_rgb()
    if result is None:
        return
    r, g, b, px1, py1, px2, py2, viewer_node = result

    title = None
    create_constant = False

    if ask_options:
        panel = nuke.Panel("Sample HSVL")
        panel.addSingleLineInput("Label (optional):", "")
        panel.addBooleanCheckBox("Also create Constant node", _last_create_constant)

        if not panel.show():
            return

        title_input = panel.value("Label (optional):").strip()
        title = title_input or None
        create_constant = bool(panel.value("Also create Constant node"))
        _last_create_constant = create_constant

    _create_hsvl_sticky(r, g, b, px1, py1, px2, py2, viewer_node, title=title, create_constant=create_constant)


def sample_hsvl_quick():
    """Quick sample ROI to StickyNote without dialog (Ctrl+Shift+Alt+Enter)."""
    sample_hsvl_to_sticky(ask_options=False)


# ─── Menu registration ───────────────────────────────────────────────────────

if nuke.env.get("gui"):
    _viewer_menu  = nuke.menu("Viewer")
    _hsvl_menu    = _viewer_menu.addMenu("HSVL Sampler", icon="StickyNote.png")

    _hsvl_menu.addCommand(
        "-> Quick Sample HSVL (Instant StickyNote)",
        "import SR_HSVLfromROI; SR_HSVLfromROI.sample_hsvl_quick()",
        "ctrl+shift+return",
        icon="StickyNote.png",
    )
    _hsvl_menu.addCommand(
        "-> Sample HSVL with Options (Label & Constant)",
        "import SR_HSVLfromROI; SR_HSVLfromROI.sample_hsvl_to_sticky()",
        "ctrl+shift+alt+return",
        icon="StickyNote.png",
    )
