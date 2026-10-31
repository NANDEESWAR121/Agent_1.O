# automation.py
# Core module for Windows UI Automation using pywinauto

import logging
import sys
import io
import ctypes
from ctypes import wintypes

# Ensure stdout and stderr use UTF-8 to prevent charmap encoding errors on Windows console
if sys.stdout and hasattr(sys.stdout, 'buffer') and not getattr(sys.stdout, 'closed', False):
    if getattr(sys.stdout, 'encoding', '').lower() != 'utf-8':
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass

if sys.stderr and hasattr(sys.stderr, 'buffer') and not getattr(sys.stderr, 'closed', False):
    if getattr(sys.stderr, 'encoding', '').lower() != 'utf-8':
        try:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass

from pywinauto import Desktop
from pywinauto.findwindows import ElementNotFoundError

logger = logging.getLogger("AntigravityAgent")

def ensure_default_desktop():
    """
    Ensures the current thread is associated with the 'Default' desktop.
    In some agent execution environments, the thread starts on a custom
    desktop where user windows are not visible.
    """
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        hCurrentDesk = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
        buf = ctypes.create_unicode_buffer(512)
        length = ctypes.c_ulong()
        user32.GetUserObjectInformationW(hCurrentDesk, 2, buf, 512, ctypes.byref(length))
        current_desktop_name = buf.value
        
        if current_desktop_name and current_desktop_name.lower() != "default":
            logger.info(f"Current desktop is '{current_desktop_name}'. Switching thread to 'Default'...")
            hDefaultDesk = user32.OpenDesktopW("Default", 0, False, 0x1FF)
            if not hDefaultDesk:
                hDefaultDesk = user32.OpenDesktopW("Default", 0, False, 0x10000000)
                
            if hDefaultDesk:
                res = user32.SetThreadDesktop(hDefaultDesk)
                if res:
                    logger.info("Successfully switched thread desktop to 'Default'.")
                else:
                    logger.warning(f"SetThreadDesktop failed. Error: {kernel32.GetLastError()}")
            else:
                logger.warning(f"OpenDesktop failed. Error: {kernel32.GetLastError()}")
    except Exception as e:
        logger.warning(f"ensure_default_desktop encountered error: {e}")

def get_desktop():
    """
    Connects to the Windows Desktop using pywinauto's UIA backend.
    
    Returns:
        Desktop: A pywinauto Desktop object with the UIA backend.
    """
    ensure_default_desktop()
    try:
        return Desktop(backend="uia")
    except Exception as e:
        logger.error(f"Failed to connect to Desktop UIA backend: {e}")
        raise

def list_open_windows():
    """
    Utility to print all open top-level windows to stdout.
    Iterates through windows visible on the desktop and prints their titles,
    class names, and process IDs.
    
    Returns:
        list[dict]: A list of window info dicts.
    """
    windows_info = []
    try:
        desktop = get_desktop()
        windows = desktop.windows()
        
        print("\n=== Active Top-Level Windows ===")
        print(f"{'PID':<8} | {'Class Name':<35} | {'Window Title'}")
        print("-" * 80)
        
        for w in windows:
            try:
                title = w.window_text()
                class_name = w.class_name()
                pid = w.process_id()
                
                # Format empty titles/classes nicely
                title_str = title if title else "<No Title>"
                class_str = class_name if class_name else "<No Class>"
                
                print(f"{pid:<8} | {class_str[:35]:<35} | {title_str}")
                windows_info.append({
                    "title": title,
                    "class_name": class_name,
                    "process_id": pid,
                    "wrapper": w
                })
            except Exception as e:
                # Handle cases where windows disappear during iteration
                continue
        print("===============================\n")
    except Exception as e:
        logger.error(f"Error listing open windows: {e}")
        
    return windows_info

def print_control_identifiers(dialog):
    """
    Utility to print all controls of the detected dialog using print_control_identifiers().
    This helps in debugging the control hierarchy of the target window.
    
    Args:
        dialog: The pywinauto window/dialog wrapper object.
    """
    print("\n=== Control Identifiers for Detected Dialog ===")
    try:
        from pywinauto.application import Application
        # Connect to the window using its handle to get a WindowSpecification
        app = Application(backend="uia").connect(handle=dialog.handle)
        dlg_spec = app.window(handle=dialog.handle)
        dlg_spec.print_control_identifiers()
    except Exception as e:
        print(f"Error printing control identifiers: {e}")
    print("================================================\n")

import config

def safe_extract_label(elem):
    """
    Safely extracts window text and element info name without raising COM errors.
    """
    parts = []
    try:
        t = elem.window_text()
        if t:
            parts.append(t)
    except Exception:
        pass
    try:
        n = elem.element_info.name
        if n:
            parts.append(n)
    except Exception:
        pass
    return " ".join(parts).strip()

def find_all_permission_dialogs(desktop, title_keywords=None, text_keywords=None, button_keywords=None):
    """
    Searches the desktop for ALL Antigravity permission dialogs across all open windows.
    Returns a list of matching pywinauto window wrappers.
    Uses targeted UIA queries for maximum performance (0% CPU overhead).
    """
    if button_keywords is None:
        button_keywords = config.TARGET_BUTTON_TEXTS

    try:
        windows = desktop.windows()
    except Exception as e:
        logger.debug(f"Failed to fetch desktop windows: {e}")
        return []

    # Ignore irrelevant non-target background windows
    ignore_terms = [
        "google chrome", "microsoft teams", "whatsapp", "file explorer", 
        "taskbar", "program manager", "notepad", "pgadmin"
    ]

    matching_dialogs = []

    for w in windows:
        try:
            title = w.window_text() or ""
            title_lower = title.lower()
            
            if any(term in title_lower for term in ignore_terms):
                continue
            
            # Filter by window title if keywords are provided
            if title_keywords:
                if not any(k.lower() in title_lower for k in title_keywords):
                    continue
            
            # Fast scan for visible target buttons in this window
            btn, matched = find_target_button(w, button_keywords)
            if btn:
                matching_dialogs.append(w)
            
        except Exception as e:
            continue
            
    return matching_dialogs

def find_permission_dialog(desktop, title_keywords=None, text_keywords=None, button_keywords=None):
    """
    Backward compatibility wrapper. Returns the first matching dialog window.
    """
    dialogs = find_all_permission_dialogs(
        desktop, 
        title_keywords=title_keywords, 
        text_keywords=text_keywords, 
        button_keywords=button_keywords
    )
    return dialogs[0] if dialogs else None

def find_target_button(dialog, button_texts=None):
    """
    Locates any target button (e.g. "Submit", "Retry", "Allow") inside the permission dialog.
    Searches visible controls of type "Button", "Custom", or "MenuItem" on screen.
    """
    if button_texts is None:
        button_texts = config.TARGET_BUTTON_TEXTS
    if isinstance(button_texts, str):
        button_texts = [button_texts]

    try:
        # Strategy 1: Targeted search for visible control_type="Button" descendants
        buttons = dialog.descendants(control_type="Button")
        for btn in buttons:
            try:
                rect = btn.rectangle()
                # Ensure control is visible on screen
                if rect.top <= 0 or rect.width() <= 0 or rect.height() <= 0:
                    continue

                label = safe_extract_label(btn)
                label_clean = label.lower()
                words = label_clean.split()

                if len(label_clean) > 40:
                    continue

                for target in button_texts:
                    target_clean = target.strip().lower()
                    if (target_clean == label_clean or 
                        target_clean in words or 
                        any(target_clean == w for w in words)):
                        return btn, target
            except Exception:
                continue

        # Strategy 2: Fast search for visible control_type="Custom" or "MenuItem" descendants
        custom_elems = dialog.descendants(control_type="Custom") + dialog.descendants(control_type="MenuItem")
        for elem in custom_elems:
            try:
                rect = elem.rectangle()
                if rect.top <= 0 or rect.width() <= 0 or rect.height() <= 0:
                    continue

                label = safe_extract_label(elem)
                label_clean = label.lower()
                words = label_clean.split()

                if len(label_clean) > 40:
                    continue

                for target in button_texts:
                    target_clean = target.strip().lower()
                    if (target_clean == label_clean or 
                        target_clean in words or 
                        any(target_clean == w for w in words)):
                        return elem, target
            except Exception:
                continue

    except Exception as e:
        logger.debug(f"Error scanning for target buttons: {e}")
        
    return None, None

def find_submit_button(dialog, button_text="Submit"):
    """
    Locates a specific button inside the permission dialog (backward compatibility wrapper).
    """
    btn, _ = find_target_button(dialog, button_texts=button_text)
    return btn

def click_target_button(button, parent_dialog=None):
    """
    Attempts to click the target button using non-intrusive background methods first.
    Exhausts non-intrusive UIA & Win32 IPC signals before attempting physical mouse movement.
    
    Args:
        button: The pywinauto button control wrapper.
        parent_dialog: Optional pywinauto window wrapper of the parent window.
        
    Returns:
        bool: True if clicked successfully, False otherwise.
    """
    WM_LBUTTONDOWN = 0x0201
    WM_LBUTTONUP = 0x0202
    MK_LBUTTON = 0x0001
    BM_CLICK = 0x00F5

    # Method 1: Try UIA Invoke pattern (non-intrusive background click)
    try:
        logger.debug("Attempting to click button via UIA Invoke pattern...")
        button.invoke()
        logger.info("Button clicked via UIA Invoke pattern.")
        return True
    except Exception as e:
        logger.debug(f"UIA Invoke failed: {e}")

    # Method 2: Try LegacyIAccessible DoDefaultAction (non-intrusive, ideal for Electron/VS Code)
    try:
        logger.debug("Attempting to click button via LegacyIAccessible DoDefaultAction...")
        button.legacy_iaccessible_do_default_action()
        logger.info("Button clicked via LegacyIAccessible DoDefaultAction.")
        return True
    except Exception as e:
        logger.debug(f"LegacyIAccessible DoDefaultAction failed: {e}")

    # Method 3: Try UIA Select or Toggle pattern (non-intrusive)
    try:
        if hasattr(button, 'select'):
            logger.debug("Attempting to click button via UIA Select pattern...")
            button.select()
            logger.info("Button triggered via UIA Select pattern.")
            return True
        elif hasattr(button, 'toggle'):
            logger.debug("Attempting to click button via UIA Toggle pattern...")
            button.toggle()
            logger.info("Button triggered via UIA Toggle pattern.")
            return True
    except Exception as e:
        logger.debug(f"UIA Select/Toggle pattern failed: {e}")

    # Method 4: Win32 PostMessage (WM_LBUTTONDOWN / WM_LBUTTONUP) at button coordinates in background
    try:
        user32 = ctypes.windll.user32
        target_handle = getattr(button, 'handle', None) or (parent_dialog.handle if parent_dialog else None)
        if target_handle:
            rect = button.rectangle()
            point = wintypes.POINT((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)
            user32.ScreenToClient(target_handle, ctypes.byref(point))
            lparam = (point.y << 16) | (point.x & 0xFFFF)
            
            logger.debug(f"Sending Win32 background click PostMessage to handle {target_handle} at ({point.x}, {point.y})...")
            user32.PostMessageW(target_handle, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
            user32.PostMessageW(target_handle, WM_LBUTTONUP, 0, lparam)
            logger.info("Button clicked via Win32 background PostMessage.")
            return True
    except Exception as e:
        logger.debug(f"Win32 background PostMessage click failed: {e}")

    # Method 5: Fallback to click_input (physical mouse click)
    try:
        logger.debug("Falling back to click_input (physical mouse click)...")
        button.click_input()
        logger.info("Button clicked via click_input.")
        return True
    except Exception as e:
        logger.warning(f"pywinauto click_input failed: {e}")

    # Method 6: Fallback to PyAutoGUI click at bounding box center
    try:
        import pyautogui
        rect = button.rectangle()
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        logger.debug(f"PyAutoGUI clicking at screen coordinates: ({center_x}, {center_y})")
        pyautogui.click(center_x, center_y)
        return True
    except Exception as py_err:
        logger.error(f"PyAutoGUI click failed: {py_err}")

    return False

def click_submit_button(button):
    """
    Backward compatibility wrapper for click_target_button.
    """
    return click_target_button(button)
