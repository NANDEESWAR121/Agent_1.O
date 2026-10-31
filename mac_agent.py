# mac_agent.py
# macOS UI Automation Agent for Antigravity Desktop Application
# Uses macOS Accessibility & System Events via AppleScript (osascript)

import sys
import time
import subprocess
import logging
import config

logger = logging.getLogger("AntigravityAgent")

def build_applescript_search_and_click(button_targets):
    """
    Builds an AppleScript to inspect Antigravity desktop windows
    and click matching target buttons (e.g. Submit, Retry, Allow).
    """
    # Format button targets as an AppleScript list
    escaped_buttons = [f'"{b.strip()}"' for b in button_targets]
    buttons_as_str = ", ".join(escaped_buttons)
    
    script = f'''
tell application "System Events"
    set targetButtonList to {{{buttons_as_str}}}
    set matchedApps to {{}}
    
    -- 1. Locate Antigravity by process name
    repeat with p in (every application process whose background only is false)
        try
            set procName to name of p as string
            if procName contains "Antigravity" or procName contains "antigravity" then
                set end of matchedApps to p
            end if
        end try
    end repeat
    
    -- 2. If not found by process name, locate by window titles
    if (count of matchedApps) is 0 then
        repeat with p in (every application process whose background only is false)
            try
                repeat with w in (every window of p)
                    set wTitle to (name of w as string)
                    if wTitle contains "Antigravity" then
                        set end of matchedApps to p
                        exit repeat
                    end if
                end repeat
            end try
        end repeat
    end if
    
    -- 3. Search and click target buttons in identified windows & sheets
    repeat with p in matchedApps
        tell p
            repeat with w in (every window)
                -- Direct window buttons
                repeat with bName in targetButtonList
                    try
                        set matchedBtn to (first button of w whose name is bName or title is bName or description is bName)
                        click matchedBtn
                        return "Clicked button '" & bName & "' in window '" & (name of w as string) & "'"
                    end try
                end repeat
                
                -- Sheets / Modal sheets
                repeat with s in (every sheet of w)
                    repeat with bName in targetButtonList
                        try
                            set matchedBtn to (first button of s whose name is bName or title is bName or description is bName)
                            click matchedBtn
                            return "Clicked sheet button '" & bName & "'"
                        end try
                    end repeat
                end repeat
                
                -- Modal Dialogs / UI Elements
                repeat with el in (every UI element of w)
                    repeat with bName in targetButtonList
                        try
                            if role of el is "AXButton" and (name of el is bName or title of el is bName) then
                                click el
                                return "Clicked dialog button '" & bName & "'"
                            end if
                        end try
                    end repeat
                end repeat
            end repeat
        end tell
    end repeat
    
    return "NO_DIALOG"
end tell
'''
    return script

def list_open_mac_windows():
    """
    Lists all open macOS application windows with process names and titles.
    """
    script = '''
tell application "System Events"
    set outText to ""
    repeat with p in (every application process whose background only is false)
        try
            set pName to name of p
            set pId to unix id of p
            repeat with w in (every window of p)
                set wTitle to name of w
                if wTitle is not "" then
                    set outText to outText & (pId as string) & " | " & pName & " | " & wTitle & linefeed
                end if
            end repeat
        end try
    end repeat
    return outText
end tell
'''
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        lines = res.stdout.strip().split("\n")
        print("\n=== Active Top-Level Windows (macOS) ===")
        print(f"{'PID':<8} | {'Process Name':<25} | {'Window Title'}")
        print("-" * 80)
        for line in lines:
            parts = line.split(" | ")
            if len(parts) >= 3:
                pid, proc, title = parts[0], parts[1], " | ".join(parts[2:])
                print(f"{pid:<8} | {proc[:25]:<25} | {title}")
        print("=========================================\n")
    except Exception as e:
        logger.error(f"Error listing macOS windows: {e}")

def run_mac_watcher(print_controls_on_detect=False, button_targets=None):
    """
    Continuously monitors the Antigravity desktop application on macOS
    and automatically clicks matched permission / retry / allow buttons.
    """
    if button_targets is None:
        target_buttons = config.TARGET_BUTTON_TEXTS
    elif isinstance(button_targets, str):
        target_buttons = [button_targets]
    else:
        target_buttons = list(button_targets)

    poll_interval_sec = config.POLLING_INTERVAL_MS / 1000.0

    logger.info("Starting Antigravity macOS Desktop Automation Watcher...")
    logger.info(f"Polling interval set to {config.POLLING_INTERVAL_MS} ms.")
    logger.info(f"Target buttons: {target_buttons}")
    logger.info("Monitoring for Antigravity desktop application dialogs...")
    print("Waiting for dialogs across Antigravity desktop windows (Press Ctrl+C to stop)...")

    script = build_applescript_search_and_click(target_buttons)

    while True:
        try:
            res = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if res.returncode == 0:
                output = res.stdout.strip()
                if output and output != "NO_DIALOG":
                    logger.info(f"Auto-action executed: {output}")
            else:
                stderr = res.stderr.strip()
                # Check for macOS Accessibility permission error
                if "1743" in stderr or "not allowed" in stderr.lower() or "accessibility" in stderr.lower():
                    logger.critical(
                        "macOS Accessibility Permission Required!\n"
                        "Please go to: System Settings -> Privacy & Security -> Accessibility\n"
                        "and enable Terminal (or Python) to allow window automation."
                    )
                    time.sleep(5)
                elif stderr:
                    logger.debug(f"osascript error: {stderr}")

        except KeyboardInterrupt:
            logger.info("Watcher interrupted by user. Shutting down gracefully.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in macOS watcher: {e}")

        time.sleep(poll_interval_sec)
