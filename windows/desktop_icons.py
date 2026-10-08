import os
import random
from core.config import WIN32_AVAILABLE, WINSHELL_AVAILABLE

if WIN32_AVAILABLE:
    import win32gui
    import win32process
    import ctypes
    import ctypes.wintypes

if WINSHELL_AVAILABLE:
    import winshell

class DesktopIconMover:
    LVM_GETITEMCOUNT    = 0x1004
    LVM_GETITEMPOSITION = 0x1010
    LVM_SETITEMPOSITION32 = 0x101A
    LVM_ARRANGE         = 0x1016
    PROCESS_ALL_ACCESS  = 0x001F0FFF
    MEM_COMMIT_RESERVE  = 0x3000
    MEM_RELEASE         = 0x8000
    PAGE_READWRITE      = 0x04

    def __init__(self):
        self.listview_hwnd = None
        if WIN32_AVAILABLE:
            self._init_handles()

    def _init_handles(self):
        lv = [None]
        def _find_lv(hwnd, _):
            if lv[0]:
                return
            defview = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
            if defview:
                lv[0] = win32gui.FindWindowEx(defview, 0, "SysListView32", None)
        win32gui.EnumWindows(_find_lv, None)
        if not lv[0]:
            progman = win32gui.FindWindow("Progman", None)
            defview = win32gui.FindWindowEx(progman, 0, "SHELLDLL_DefView", None)
            if defview:
                lv[0] = win32gui.FindWindowEx(defview, 0, "SysListView32", None)
        self.listview_hwnd = lv[0]

    def _open_desktop_proc(self):
        if not self.listview_hwnd:
            return None, None
        _, pid = win32process.GetWindowThreadProcessId(self.listview_hwnd)
        hproc = ctypes.windll.kernel32.OpenProcess(self.PROCESS_ALL_ACCESS, False, pid)
        return hproc, pid

    def _item_count(self):
        if not self.listview_hwnd:
            return 0
        return ctypes.windll.user32.SendMessageW(self.listview_hwnd, self.LVM_GETITEMCOUNT, 0, 0)

    def _get_pos(self, hproc, idx):
        pt_size = ctypes.sizeof(ctypes.wintypes.POINT)
        buf = ctypes.windll.kernel32.VirtualAllocEx(
            hproc, None, pt_size, self.MEM_COMMIT_RESERVE, self.PAGE_READWRITE)
        if not buf:
            return None
        try:
            ctypes.windll.user32.SendMessageW(self.listview_hwnd, self.LVM_GETITEMPOSITION, idx, buf)
            pt = ctypes.wintypes.POINT()
            read = ctypes.c_size_t()
            ctypes.windll.kernel32.ReadProcessMemory(
                hproc, buf, ctypes.byref(pt), pt_size, ctypes.byref(read))
            return pt.x, pt.y
        finally:
            ctypes.windll.kernel32.VirtualFreeEx(hproc, buf, 0, self.MEM_RELEASE)

    def _set_pos(self, hproc, idx, x, y):
        pt_size = ctypes.sizeof(ctypes.wintypes.POINT)
        buf = ctypes.windll.kernel32.VirtualAllocEx(
            hproc, None, pt_size, self.MEM_COMMIT_RESERVE, self.PAGE_READWRITE)
        if not buf:
            return False
        try:
            pt = ctypes.wintypes.POINT(int(x), int(y))
            written = ctypes.c_size_t()
            ctypes.windll.kernel32.WriteProcessMemory(
                hproc, buf, ctypes.byref(pt), pt_size, ctypes.byref(written))
            ctypes.windll.user32.SendMessageW(self.listview_hwnd, self.LVM_SETITEMPOSITION32, idx, buf)
            return True
        finally:
            ctypes.windll.kernel32.VirtualFreeEx(hproc, buf, 0, self.MEM_RELEASE)

    def shuffle_icons(self):
        if not WIN32_AVAILABLE:
            return False
        hproc, _ = self._open_desktop_proc()
        if not hproc:
            return False
        try:
            count = self._item_count()
            if count == 0:
                return False
            positions = []
            for i in range(count):
                pos = self._get_pos(hproc, i)
                if pos:
                    positions.append(pos)
                else:
                    positions.append((100 + (i % 10) * 80, 100 + (i // 10) * 80))
            shuffled = list(positions)
            random.shuffle(shuffled)
            for i, (nx, ny) in enumerate(shuffled):
                self._set_pos(hproc, i, nx, ny)
            return True
        finally:
            ctypes.windll.kernel32.CloseHandle(hproc)

    def scatter_icons(self):
        if not WIN32_AVAILABLE:
            return False
        hproc, _ = self._open_desktop_proc()
        if not hproc:
            return False
        try:
            count = self._item_count()
            if count == 0:
                return False
            sw = ctypes.windll.user32.GetSystemMetrics(0)
            sh = ctypes.windll.user32.GetSystemMetrics(1)
            for i in range(count):
                nx = random.randint(40, max(40, sw - 120))
                ny = random.randint(40, max(40, sh - 120))
                self._set_pos(hproc, i, nx, ny)
            return True
        finally:
            ctypes.windll.kernel32.CloseHandle(hproc)

    def sort_icons_grid(self):
        if not WIN32_AVAILABLE or not self.listview_hwnd:
            return False
        ctypes.windll.user32.SendMessageW(self.listview_hwnd, self.LVM_ARRANGE, 0, 0)
        return True

    def _get_icon_name(self, hproc, idx):
        LVIF_TEXT = 0x0001
        LVM_GETITEMTEXTW = 0x1073
        TEXT_BUF_CHARS = 260
        TEXT_BUF_BYTES = TEXT_BUF_CHARS * 2

        class LVITEMW(ctypes.Structure):
            _fields_ = [
                ("mask",       ctypes.c_uint),
                ("iItem",      ctypes.c_int),
                ("iSubItem",   ctypes.c_int),
                ("state",      ctypes.c_uint),
                ("stateMask",  ctypes.c_uint),
                ("pszText",    ctypes.c_void_p),
                ("cchTextMax", ctypes.c_int),
                ("iImage",     ctypes.c_int),
                ("lParam",     ctypes.c_ssize_t),
                ("iIndent",    ctypes.c_int),
                ("iGroupId",   ctypes.c_int),
                ("cColumns",   ctypes.c_uint),
                ("puColumns",  ctypes.c_void_p),
                ("piColFmt",   ctypes.c_void_p),
                ("iGroup",     ctypes.c_int),
            ]

        struct_size = ctypes.sizeof(LVITEMW)
        total_size = struct_size + TEXT_BUF_BYTES
        remote_buf = ctypes.windll.kernel32.VirtualAllocEx(
            hproc, None, total_size, self.MEM_COMMIT_RESERVE, self.PAGE_READWRITE)
        if not remote_buf:
            return f"Значок #{idx + 1}"
        try:
            remote_text_buf = remote_buf + struct_size
            item = LVITEMW()
            item.mask = LVIF_TEXT
            item.iItem = idx
            item.iSubItem = 0
            item.pszText = ctypes.c_void_p(remote_text_buf)
            item.cchTextMax = TEXT_BUF_CHARS

            written = ctypes.c_size_t()
            ctypes.windll.kernel32.WriteProcessMemory(
                hproc, remote_buf, ctypes.byref(item), struct_size, ctypes.byref(written))

            chars_read = ctypes.windll.user32.SendMessageW(
                self.listview_hwnd, LVM_GETITEMTEXTW, idx, remote_buf)
            if chars_read > 0:
                raw_bytes = (ctypes.c_char * (chars_read * 2))()
                nread = ctypes.c_size_t()
                ctypes.windll.kernel32.ReadProcessMemory(
                    hproc, remote_text_buf, ctypes.byref(raw_bytes),
                    chars_read * 2, ctypes.byref(nread))
                return bytes(raw_bytes).decode("utf-16le", errors="replace").rstrip("\x00")
            return f"Значок #{idx + 1}"
        except Exception:
            return f"Значок #{idx + 1}"
        finally:
            ctypes.windll.kernel32.VirtualFreeEx(hproc, remote_buf, 0, self.MEM_RELEASE)

    def get_icon_list(self):
        if not WIN32_AVAILABLE:
            return []
        hproc, _ = self._open_desktop_proc()
        if not hproc:
            return []
        try:
            count = self._item_count()
            icons = []
            for i in range(count):
                name = self._get_icon_name(hproc, i)
                icons.append((i, name))
            return icons
        finally:
            ctypes.windll.kernel32.CloseHandle(hproc)

    def move_one_icon(self, idx):
        if not WIN32_AVAILABLE:
            return False
        hproc, _ = self._open_desktop_proc()
        if not hproc:
            return False
        try:
            sw = ctypes.windll.user32.GetSystemMetrics(0)
            sh = ctypes.windll.user32.GetSystemMetrics(1)
            nx = random.randint(40, max(40, sw - 120))
            ny = random.randint(40, max(40, sh - 120))
            return self._set_pos(hproc, idx, nx, ny)
        finally:
            ctypes.windll.kernel32.CloseHandle(hproc)

    def trash_icon_at_index(self, idx):
        if not WIN32_AVAILABLE:
            return False, "pywin32 не доступен"
        if not WINSHELL_AVAILABLE:
            return False, "winshell не установлен"
        hproc, _ = self._open_desktop_proc()
        if not hproc:
            return False, "Не удалось открыть процесс рабочего стола"
        name = ""
        try:
            name = self._get_icon_name(hproc, idx)
        finally:
            ctypes.windll.kernel32.CloseHandle(hproc)

        desktop_paths = [
            winshell.desktop(),
            winshell.desktop(common=1)
        ]
        target_file = None
        for dp in desktop_paths:
            if not os.path.exists(dp):
                continue
            for f in os.listdir(dp):
                stem, _ = os.path.splitext(f)
                if f == name or stem == name or name in f:
                    candidate = os.path.join(dp, f)
                    if os.path.exists(candidate):
                        target_file = candidate
                        break
            if target_file:
                break

        if not target_file:
            return False, f"Файл '{name}' не найден на рабочем столе"

        try:
            from win32com.shell import shell, shellcon
            res, _ = shell.SHFileOperation((
                0,
                shellcon.FO_DELETE,
                target_file + "\x00",
                None,
                shellcon.FOF_ALLOWUNDO | shellcon.FOF_NOCONFIRMATION | shellcon.FOF_SILENT,
                None,
                None
            ))
            if res == 0:
                return True, name
            return False, f"Ошибка SHFileOperation: {res}"
        except Exception as e:
            return False, str(e)
