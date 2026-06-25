# Contents
- [Taskbar badge](#taskbar-badge)
- [How does it work](#how-does-it-work)
- [Setup](#setup)
- [Running the widget](#running-the-widget)
- [Closing the widget](#closing-the-widget)
# Taskbar badge
Small application to show a widget on top of the Windows 11 taskbar. Currently only designed to work with taskbar position set to centre.

<img src=./assets/screenshot.png>

## How does it work
Microsoft do not provide any API for building applications that live on the Windows 11 taskbar (https://learn.microsoft.com/en-us/windows/configuration/taskbar/?pivots=windows-11). As a workaround, we can manipulate the TOPMOST Windows property to force a widget to be painted last (i.e., on top of everything else). Combined with positioning the widget within the bounds of the taskbar rect, this creates the illusion of a native taskbar widget. The below method is the application's implementation of this 'hack':
```
def set_widget_top_most(self, widget):
    """
    Leverage the Windows API's SetWindowPos method to force
    this application to be placed on top of the taskbar
    --> BOOL SetWindowPos(
            HWND hWnd,
            HWND hWndInsertAfter,
            int X,
            int Y,
            int cx,
            int cy,
            UINT uFlags
        );
    """
    # Win32-level bump (more reliable vs taskbar)
    if sys.platform == "win32" and widget.isVisible(): # Only Windows supported for now
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        HWND_TOPMOST = -1       # -1 forces windows to place this window in the topmost Z-order
        SWP_NOMOVE = 0x0002     # Keep x-y position fixed when painting
        SWP_NOSIZE = 0x0001     # Keep size fixed when painting
        SWP_NOACTIVATE = 0x0010 # Don't steal focus
        SWP_SHOWWINDOW = 0x0040 # Ensure the window is visible after SetWindowPos

        user32.SetWindowPos(
            wintypes.HWND(int(widget.winId())), # This window's window handle
            wintypes.HWND(HWND_TOPMOST), # Make this window permanently TOPMOST
            0, 0, 0, 0, # x, y, x_width, y_width (all ignored because of below flags)

            # Combine all flags together into 'uFlags'
            SWP_NOMOVE |
            SWP_NOSIZE |
            SWP_NOACTIVATE |
            SWP_SHOWWINDOW
        )
```

## Setup
Open `config.yml` in a text editor:
- Set `text` to the desired display text. Set to 'null' to use the PC's hostname
- Set `bg_colour` to the desired background colour of the widget
- Set `fg_colour` to the desired foreground (text) colour of the widget
- Set `border_radius` to the desired border radius of the widget

## Running the widget
The widget is currently only executable via Python. An .exe version will be included in future

## Closing the widget
Close the widget by either:
- Holding `CTRL` and `SHIFT` and left-clicking the widget
- Right clicking the widget and pressing the `Close` option that pops up

