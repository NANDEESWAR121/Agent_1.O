# main.py
# Main entry point for the Antigravity Desktop UI Automation Agent
# Supports Windows (via pywinauto / UIA) and macOS (via AppleScript / System Events)

import sys
import argparse
import logging
import config

# Platform-specific initialization
IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

if IS_WINDOWS:
    import ctypes
    from ctypes import wintypes

    def ensure_default_desktop():
        """
        Ensures the current thread is associated with the 'Default' desktop on Windows.
        """
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            
            hCurrentDesk = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
            UOI_NAME = 2
            buf = ctypes.create_unicode_buffer(512)
            length = ctypes.c_ulong()
            user32.GetUserObjectInformationW(hCurrentDesk, UOI_NAME, buf, 512, ctypes.byref(length))
            current_desktop_name = buf.value
            
            if current_desktop_name and current_desktop_name.lower() != "default":
                print(f"Agent: Current desktop is '{current_desktop_name}'. Switching thread to 'Default'...")
                hDefaultDesk = user32.OpenDesktopW("Default", 0, False, 0x1FF)
                if not hDefaultDesk:
                    hDefaultDesk = user32.OpenDesktopW("Default", 0, False, 0x10000000)
                    
                if hDefaultDesk:
                    res = user32.SetThreadDesktop(hDefaultDesk)
                    if res:
                        print("Agent: Successfully switched thread desktop to 'Default'.")
                    else:
                        print(f"Agent WARNING: SetThreadDesktop failed. Error: {kernel32.GetLastError()}")
                else:
                    print(f"Agent WARNING: OpenDesktop failed. Error: {kernel32.GetLastError()}")
        except Exception as e:
            print(f"Agent WARNING: ensure_default_desktop error: {e}")

    ensure_default_desktop()
    from watcher import run_watcher
    from automation import (
        list_open_windows,
        get_desktop,
        find_permission_dialog,
        print_control_identifiers
    )

elif IS_MACOS:
    import mac_agent


def setup_logging():
    """
    Configures basic logging for the agent.
    If config.DEBUG_MODE is True, it sets the log level to DEBUG.
    """
    log_level = logging.DEBUG if config.DEBUG_MODE else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """
    Main orchestrator that parses command-line arguments and routes execution to the watcher or diagnostic utilities.
    """
    setup_logging()
    logger = logging.getLogger("AntigravityAgent")
    
    # -------------------------------------------------------------
    # 1. Agent Initialization
    # -------------------------------------------------------------
    os_name = "macOS" if IS_MACOS else ("Windows" if IS_WINDOWS else sys.platform)
    logger.info(f"Antigravity Desktop Agent initialized on {os_name}.")
    
    # -------------------------------------------------------------
    # 2. Automation Engine & Utilities Flow
    # -------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Desktop UI Automation Agent for the Antigravity Permission Dialog (Windows & macOS)."
    )
    
    group = parser.add_mutually_exclusive_group()
    
    group.add_argument(
        "--watch",
        action="store_true",
        default=True,
        help="Start the agent to monitor for the permission dialog and click target buttons (Default)."
    )
    
    group.add_argument(
        "--list-windows",
        action="store_true",
        help="Utility to list all open top-level windows with their process IDs and titles."
    )
    
    group.add_argument(
        "--print-controls",
        action="store_true",
        help="Utility to search for an active permission dialog and print all of its control identifiers (Windows only)."
    )
    
    parser.add_argument(
        "--print-controls-on-detect",
        action="store_true",
        help="If watching, print the controls of the permission dialog the first time it is detected."
    )

    parser.add_argument(
        "--buttons",
        nargs="+",
        default=None,
        help="Custom list of target button names/texts to search for and click (e.g. Submit Retry Allow)."
    )
    
    args = parser.parse_args()
    
    is_watch = args.watch
    if args.list_windows or args.print_controls:
        is_watch = False

    # Route: List Windows
    if args.list_windows:
        if IS_MACOS:
            mac_agent.list_open_mac_windows()
        elif IS_WINDOWS:
            print("Listing all open top-level windows...")
            list_open_windows()
        else:
            print(f"Listing windows not supported on {sys.platform}.")
        sys.exit(0)
        
    # Route: Print Controls
    elif args.print_controls:
        if IS_MACOS:
            print("Control tree inspection via --print-controls is specific to Windows UIA.")
            print("On macOS, windows and buttons are matched dynamically via System Events.")
        elif IS_WINDOWS:
            print("Searching for the active permission dialog...")
            try:
                desktop = get_desktop()
                dialog = find_permission_dialog(
                    desktop,
                    title_keywords=config.WINDOW_TITLE_KEYWORDS,
                    text_keywords=config.DIALOG_TEXT_KEYWORDS,
                    button_keywords=args.buttons
                )
                
                if dialog:
                    print("Permission dialog found!")
                    print_control_identifiers(dialog)
                else:
                    print("Permission dialog NOT found.")
                    print("Make sure the dialog is open and matches the keywords in config.py.")
            except Exception as e:
                print(f"Error printing controls: {e}")
        sys.exit(0)
        
    # Route: Watcher Loop (Default)
    elif is_watch:
        if IS_MACOS:
            mac_agent.run_mac_watcher(
                print_controls_on_detect=args.print_controls_on_detect,
                button_targets=args.buttons
            )
        elif IS_WINDOWS:
            run_watcher(
                print_controls_on_detect=args.print_controls_on_detect,
                button_targets=args.buttons
            )
        else:
            logger.critical(f"Unsupported operating system: {sys.platform}. Only Windows and macOS are supported.")
            sys.exit(1)

if __name__ == "__main__":
    main()
