"""开机自启管理 - 通过注册表 Run 键实现"""
import os
import sys
import winreg


# 注册表路径
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_NAME = "历史剪贴板"


def _find_pythonw() -> str | None:
    """查找 pythonw.exe，不存在则回退到 python.exe"""
    exe_dir = os.path.dirname(sys.executable)
    # 优先 pythonw.exe（无控制台窗口）
    pythonw = os.path.join(exe_dir, "pythonw.exe")
    if os.path.isfile(pythonw):
        return pythonw
    # 回退 python.exe（会有控制台窗口闪现）
    python = os.path.join(exe_dir, "python.exe")
    if os.path.isfile(python):
        return python
    # 都找不到
    return None


def _get_project_dir() -> str:
    """获取项目根目录（startup.py 的上级目录）"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_main_py() -> str:
    """获取 main.py 的绝对路径"""
    return os.path.join(_get_project_dir(), "main.py")


def _get_startup_command() -> str:
    """获取开机自启命令行"""
    python_exe = _find_pythonw() or sys.executable  # 兜底用当前解释器
    main_py = _get_main_py()
    return f'"{python_exe}" "{main_py}" --hidden'


def validate_startup_command() -> tuple[bool, str]:
    """验证启动命令是否有效，返回 (是否有效, 错误描述)"""
    python_exe = _find_pythonw()
    if python_exe is None:
        exe_dir = os.path.dirname(sys.executable)
        return False, f"未找到 pythonw.exe 或 python.exe\n查找路径: {exe_dir}"

    main_py = _get_main_py()
    if not os.path.isfile(main_py):
        return False, f"未找到 main.py\n查找路径: {main_py}"

    return True, ""


def add_to_startup() -> tuple[bool, str]:
    """添加开机自启（写注册表），返回 (是否成功, 消息)"""
    # 先验证
    valid, err = validate_startup_command()
    if not valid:
        return False, err

    command = _get_startup_command()

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_PATH,
            0, winreg.KEY_SET_VALUE | winreg.KEY_READ,
        )
    except OSError as e:
        return False, f"无法打开注册表键: {e}"

    result = False, ""
    try:
        winreg.SetValueEx(key, REG_NAME, 0, winreg.REG_SZ, command)

        # 读回验证
        try:
            written_value, _ = winreg.QueryValueEx(key, REG_NAME)
            if written_value != command:
                result = False, f"注册表写入验证失败\n期望: {command}\n实际: {written_value}"
            else:
                result = True, "已设置开机自启"
        except FileNotFoundError:
            result = False, "注册表写入后无法读回，写入可能未生效"
    except OSError as e:
        result = False, f"写入注册表失败: {e}"
    finally:
        winreg.CloseKey(key)

    return result


def remove_from_startup() -> bool:
    """移除开机自启（删注册表键）"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_PATH,
            0, winreg.KEY_SET_VALUE,
        )
        try:
            winreg.DeleteValue(key, REG_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_startup_enabled() -> bool:
    """检查是否已设置开机自启"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_PATH,
            0, winreg.KEY_READ,
        )
        try:
            value, _ = winreg.QueryValueEx(key, REG_NAME)
            expected = _get_startup_command()
            return value == expected
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False
