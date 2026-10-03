"""Shared SR_Tools menu, loaded by Nuke from the SR_python plugin folder.

Creates SR_Tools in the top menu bar. Scripts load when clicked.
"""
import importlib
import nuke


def run_sr_tool(module_name, function_name):
    module = importlib.import_module(module_name)
    return getattr(module, function_name)()


if nuke.env.get("gui"):
    sr_tools = nuke.menu("Nuke").addMenu("SR_Tools")
    sr_tools.addCommand(
        "Bake Metadata from Read",
        lambda: run_sr_tool("SR_bakeMetadataFromRead", "bakeMeta"),
        "alt+shift+r",
        shortcutContext=2,  # Node Graph
    )
    sr_tools.addCommand(
        "HSVL/Quick Sample",
        lambda: run_sr_tool("SR_HSVLfromROI", "sample_hsvl_quick"),
    )
    sr_tools.addCommand(
        "HSVL/Sample with Options",
        lambda: run_sr_tool("SR_HSVLfromROI", "sample_hsvl_to_sticky"),
    )
    sr_tools.addCommand(
        "Open Selected Read or Write in Explorer",
        lambda: run_sr_tool("openInExplorer", "open_selected_node_in_explorer"),
        shortcutContext=2,
    )
