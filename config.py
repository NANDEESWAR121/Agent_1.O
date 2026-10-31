# config.py
# Configuration settings for the Antigravity UI Automation Agent

# Time in milliseconds to wait between checks for the permission dialog
POLLING_INTERVAL_MS = 1500

# Keywords to search for in the window titles. 
# Matches are case-insensitive. If empty, all windows will be searched.
WINDOW_TITLE_KEYWORDS = ["Antigravity", "Permission", "Confirm", "Allow", "Security", "Agent", "Error"]

# Text keywords that must be present inside the dialog text/controls
# to confirm it is the target permission or error dialog.
# Matches are case-insensitive. If empty, text keyword checking is skipped.
DIALOG_TEXT_KEYWORDS = [
    "Allow running this command?",
    "Agent terminated due to error",
    "prompt the model to try again",
    "start a new conversation",
    "access",
    "read path",
    "permission",
    "allow",
    "retry"
]

# List of target button names/texts to search for and click.
# The agent will search for any of these buttons inside detected permission/error dialogs.
TARGET_BUTTON_TEXTS = ["Submit", "Retry", "Allow"]

# Backward compatibility alias for single submit button configuration
SUBMIT_BUTTON_TEXT = "Submit"

# Whether to enable debug logging
DEBUG_MODE = True
