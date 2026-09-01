import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

class RECT(ctypes.Structure):
    _fields_=[("left",ctypes.c_long),("top",ctypes.c_long),("right",ctypes.c_long),("bottom",ctypes.c_long)]

def get_taskbar_rect():
    """Find primary taskbar (Shell_TrayWnd). Returns (left,top,right,bottom) or None"""
    hwnd = user32.FindWindowW("Shell_TrayWnd", None)
    if not hwnd:
        return None
    r = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left, r.top, r.right, r.bottom)

def get_work_area():
    """Work area = screen minus taskbar"""
    rect = RECT()
    # SPI_GETWORKAREA = 48
    ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
    return (rect.left, rect.top, rect.right, rect.bottom)

def get_screen_size():
    return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))

def get_taskbar_edge():
    """Return 'bottom','top','left','right' based on rect vs screen"""
    tr = get_taskbar_rect()
    if not tr:
        return "bottom"
    sw, sh = get_screen_size()
    l,t,r,b = tr
    w = r-l; h = b-t
    # taskbar is thin bar on one edge -> decide by comparing position
    if h < w: # horizontal
        return "bottom" if t > sh//2 else "top"
    else:
        return "right" if l > sw//2 else "left"

def calc_position(pet_w, pet_h, placement="above"):
    """
    placement: "above" = just above taskbar (floating)
               "overlay" = sitting ON the taskbar
    Returns (x,y)
    """
    tr = get_taskbar_rect()
    sw, sh = get_screen_size()
    edge = get_taskbar_edge()
    # default bottom taskbar
    if tr:
        l,t,r,b = tr
        tb_h = b - t
        tb_w = r - l
    else:
        t = sh - 40
        tb_h = 40
        l=0; r=sw; b=sh

    # horizontally: near right side, 120px from right edge (room for tray)
    x = sw - pet_w - 60
    if x < 0: x = sw - pet_w

    if placement == "above":
        # just above taskbar
        if edge == "bottom":
            y = t - pet_h - 2
        elif edge == "top":
            y = b + 2
        elif edge == "right":
            x = l - pet_w - 2
            y = sh - pet_h - 10
        else: # left
            x = r + 2
            y = sh - pet_h - 10
    else: # overlay
        if edge == "bottom":
            # overlap: bottom of pet aligns with screen bottom, centered vertically on taskbar
            y = b - pet_h + (tb_h - pet_h)//2 + 6  # tweak to sit on bar
            # clamp to not go off-screen: simpler sit ON bar
            y = sh - pet_h - 2  # exactly on bottom edge overlapping bar
        elif edge == "top":
            y = t + (tb_h - pet_h)//2
        elif edge == "right":
            x = l + (tb_w - pet_w)//2
            y = sh - pet_h - 10
        else:
            x = r - pet_w + (tb_w - pet_w)//2
            y = sh - pet_h - 10
    return (x,y)
