"""单实例检测 - 通过 PID 锁文件 + 窗口验证防止重复启动"""
import os
import ctypes

WINDOW_TITLE = "历史剪贴板"

SW_SHOW = 5
SW_RESTORE = 9


def _get_lock_path() -> str:
    """获取锁文件路径（<项目根>/data/app.lock）"""
    _project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lock_dir = os.path.join(_project_root, "data")
    os.makedirs(lock_dir, exist_ok=True)
    return os.path.join(lock_dir, "app.lock")


def _pid_is_alive(pid: int) -> bool:
    """检查指定 PID 的进程是否仍在运行"""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(0x0400, False, pid)  # PROCESS_QUERY_INFORMATION
    if handle:
        kernel32.CloseHandle(handle)
        return True
    return False


def _window_exists() -> bool:
    """检查"历史剪贴板"窗口句柄是否存在（隐藏的也能查到）"""
    user32 = ctypes.windll.user32
    return user32.FindWindowW(None, WINDOW_TITLE) != 0


def is_already_running() -> bool:
    """
    检查是否已有实例在运行。
    用「PID 存活 + 窗口存在」双重验证，任一条不满足则视为僵尸锁 → 覆盖。
    """
    lock_path = _get_lock_path()

    if os.path.exists(lock_path):
        try:
            with open(lock_path, "r") as f:
                pid = int(f.read().strip())
        except (ValueError, OSError):
            pid = None

        if pid is not None and pid != os.getpid():
            if _pid_is_alive(pid) and _window_exists():
                return True  # 真实重复实例
            # 否则：进程已死 或 窗口不存在 → 僵尸锁，覆盖

    _write_lock(lock_path)
    return False


def _write_lock(lock_path: str):
    """写入当前 PID 到锁文件"""
    try:
        with open(lock_path, "w") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass


def bring_existing_to_front() -> bool:
    """
    找到已有实例的窗口并置前显示。
    用 AttachThreadInput 突破前台窗口限制。
    """
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = user32.FindWindowW(None, WINDOW_TITLE)
    if not hwnd:
        return False

    # 突破 SetForegroundWindow 的前台锁限制
    current_thread = kernel32.GetCurrentThreadId()
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)

    attached = False
    if current_thread != target_thread:
        attached = user32.AttachThreadInput(current_thread, target_thread, True)

    # 如果最小化则恢复
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    else:
        user32.ShowWindow(hwnd, SW_SHOW)

    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)

    if attached:
        user32.AttachThreadInput(current_thread, target_thread, False)

    return True
