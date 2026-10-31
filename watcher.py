# watcher.py
# Polling and monitoring engine for the Antigravity Permission Dialog

import time
import logging
import sys
from automation import (
    get_desktop,
    find_all_permission_dialogs,
    find_target_button,
    click_target_button,
    print_control_identifiers
)
import config

logger = logging.getLogger("AntigravityAgent")

def run_watcher(print_controls_on_detect=False, button_targets=None):
    """
    Continuously monitors ALL open Windows Desktop windows for the Antigravity permission dialog.
    Checks at the interval configured in config.py (default 1500 ms).
    Clicks any matched target button (e.g. Submit, Retry, Allow) across all windows when detected.
    Exits cleanly on KeyboardInterrupt (Ctrl+C).
    
    Args:
        print_controls_on_detect (bool): If True, prints control identifiers of the dialog 
                                        upon first detection.
        button_targets (list or str): Custom list or name of target buttons to click. 
                                      Defaults to config.TARGET_BUTTON_TEXTS.
    """
    if button_targets is None:
        target_buttons = config.TARGET_BUTTON_TEXTS
    elif isinstance(button_targets, str):
        target_buttons = [button_targets]
    else:
        target_buttons = list(button_targets)

    logger.info("Starting UI Automation Watcher...")
    logger.info(f"Polling interval set to {config.POLLING_INTERVAL_MS} ms.")
    logger.info(f"Searching for dialogs containing text: {config.DIALOG_TEXT_KEYWORDS}")
    logger.info(f"Looking for buttons: {target_buttons}")
    
    # Maintain a set of processed window handles to avoid duplicate clicks
    processed_handles = set()
    
    try:
        desktop = get_desktop()
    except Exception as e:
        logger.critical(f"Unable to access the Windows desktop UIA backend. Exiting watcher: {e}")
        return

    print("Waiting for dialogs across all open windows...")
    
    while True:
        try:
            # 1. Fetch ALL matching dialog windows on desktop
            dialogs = find_all_permission_dialogs(
                desktop,
                title_keywords=config.WINDOW_TITLE_KEYWORDS,
                text_keywords=config.DIALOG_TEXT_KEYWORDS,
                button_keywords=target_buttons
            )
            
            # Update set of currently visible dialog handles
            current_handles = set()
            for dlg in dialogs:
                try:
                    current_handles.add(dlg.handle)
                except Exception:
                    current_handles.add(id(dlg))
                    
            # Remove closed/dismissed handles from processed tracking
            processed_handles = processed_handles.intersection(current_handles)
            
            if not dialogs:
                time.sleep(config.POLLING_INTERVAL_MS / 1000.0)
                continue

            # 2. Process EVERY open matching dialog window on desktop
            for dialog in dialogs:
                try:
                    handle = getattr(dialog, 'handle', id(dialog))
                    if handle in processed_handles:
                        continue
                        
                    w_title = dialog.window_text() or "Unknown Window"
                    print(f"Permission dialog detected on window: '{w_title}'")
                    
                    # Print controls utility if requested
                    if print_controls_on_detect:
                        print_control_identifiers(dialog)
                    
                    # Locate the target button in this dialog window
                    button, matched_name = find_target_button(dialog, target_buttons)
                    
                    if button is None:
                        logger.warning(f"Dialog detected in '{w_title}', but no matching target button {target_buttons} was found.")
                        processed_handles.add(handle)
                        continue
                        
                    print(f"'{matched_name}' button found in '{w_title}'.")
                    
                    # Click the button
                    clicked = click_target_button(button, parent_dialog=dialog)
                    if clicked:
                        print(f"'{matched_name}' button clicked successfully in '{w_title}'.")
                        processed_handles.add(handle)
                    else:
                        logger.error(f"Failed to click '{matched_name}' button in '{w_title}'.")
                        
                except Exception as w_err:
                    logger.error(f"Error processing dialog window: {w_err}")
                    
        except KeyboardInterrupt:
            print("\nWatcher stopped by user. Exiting cleanly...")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred in watcher loop: {e}", exc_info=True)
            logger.info("Continuing monitoring...")
            
        # Polling sleep
        try:
            time.sleep(config.POLLING_INTERVAL_MS / 1000.0)
        except KeyboardInterrupt:
            print("\nWatcher stopped by user. Exiting cleanly...")
            break
