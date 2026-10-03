# SR_Tools

Keep these files together in `~/.nuke/plugins/SR_python/`.
Add this line once to the user's existing `~/.nuke/init.py`:

```python
nuke.pluginAddPath('./plugins/SR_python')
```

Restart Nuke. Nuke loads this folder's init.py and menu.py automatically;
you do not need to copy them over the user's root setup files.
The shared menu.py owns the metadata menu command and Alt+Shift+R shortcut
(Node Graph). Importing the metadata script has no menu side effects.

HSVL commands use the active Viewer's sampling ROI. The HSVL script still
registers its original Viewer menu on import. Open in Explorer is Windows-only
and requires a selected Read or Write. Tracker export auto labelling is an
optional startup callback, commented out in menu.py.

Use the commented menu command template to add other scripts.
Python syntax checked; actual Nuke behaviour has not been tested.
