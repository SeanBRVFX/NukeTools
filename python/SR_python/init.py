"""Shared SR_python folder setup.

Enable this folder by adding the following once to ~/.nuke/init.py:
    nuke.pluginAddPath('./plugins/SR_python')
Nuke then loads this folder's init.py and menu.py automatically.
"""
import os
import sys

scripts_path = os.path.dirname(os.path.abspath(__file__))
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)
