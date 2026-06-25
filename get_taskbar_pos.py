"""
get_taskbar_pos.py

Helper file to access the Windows DLL methods
for retrieving the current setting of the Windows taskbar position
"""
import winreg
import ctypes
from ctypes import wintypes

__all__ = ["get_taskbar_pos"]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class APPBARDATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uCallbackMessage", wintypes.UINT),
        ("uEdge", wintypes.UINT),
        ("rc", RECT),
        ("lParam", wintypes.LPARAM),
    ]


def get_taskbar_position():
    """
    Retrieve the taskbar position (top, bottom, left, right) and alignment (left, center)
    """
    sh_app_bar_msg = ctypes.windll.shell32.SHAppBarMessage
    ABM_GETTTASKBARPOS = 5
    abd = APPBARDATA()
    abd.cbSize = ctypes.sizeof(APPBARDATA)

    if sh_app_bar_msg(ABM_GETTTASKBARPOS, ctypes.byref(abd)):
        edges = {
            0: "left",
            1: "top",
            2: "right",
            3: "bottom"
        }
        pos = edges[abd.uEdge]

    else:
        print("Failed to get Windows taskbar position")
        return None
    
    # Now check alignment of taskbar in its current position
    regkey = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, regkey) as key:
        try:
            taskbar_al, _ = winreg.QueryValueEx(key, "TaskbarAl")
        except FileNotFoundError:
            # If the registry key does not exist, alignment is likely the default (centre)
            taskbar_al = 1

    alignment = "left" if taskbar_al == 0 else "centre" if taskbar_al == 1 else "unknown"

    return pos, alignment
