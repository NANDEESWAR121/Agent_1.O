# Antigravity Windows UI Automation Agent

A Windows UI Automation agent built in Python using **pywinauto** (with the `"uia"` backend) to automatically detect Antigravity permission dialogs (such as command execution prompts or path access requests) and automatically click target action buttons (**Submit**, **Retry**, **Allow**).

The project features a continuous watcher that polls the desktop every 500 ms, handles exceptions gracefully without crashing, and provides diagnostic utilities for listing open windows and printing control details.

---

## Project Structure

```text
antigravity-agent/
├── main.py            # CLI entry point & diagnostics router
├── watcher.py         # Polling loop & state watcher
├── automation.py      # Core pywinauto integration (UIA controls & clicking)
├── config.py          # Configuration parameters & matching rules
├── requirements.txt   # Package dependencies
└── README.md          # Project documentation
```

---

## Features

- **Multi-Button Support**: Automatically detects and clicks **Submit**, **Retry**, or **Allow** buttons (configurable via `config.py` or `--buttons` flag).
- **Flexible Path & Command Dialog Matching**: Matches prompts for running commands as well as file/folder access permissions.
- **Reliable Clicking**: Interacts with the UIA `Button` element directly via the UIA Invoke pattern, falling back to window simulation coordinates and `PyAutoGUI` if needed.
- **Prevent Double-Clicking**: Maintains state (window handles) to ensure it only clicks a specific dialog instance once.
- **Graceful Shutdown**: Intercepts `Ctrl+C` for a clean exit.
- **Diagnostic Utilities**:
  - List all active top-level windows.
  - Print the detailed control identifier tree of the permission dialog to inspect its UIA layout.

---

## Installation

1. Ensure you have Python 3.10+ installed.
2. Open PowerShell or Command Prompt.
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1. Run the Watcher Agent (Default)
Start the agent to continuously monitor and approve the permission dialogs (clicks Submit, Retry, or Allow):
```bash
python main.py
```
*Press `Ctrl+C` at any time to exit the watcher.*

### 2. Run with Custom Target Buttons
Override default target buttons via command line argument:
```bash
python main.py --buttons Submit Retry Allow
```

### 3. Watcher with Dialog Inspection
Start the watcher and automatically output the control trees of any dialogs when they are detected (highly useful for developers debugging UIA hierarchies):
```bash
python main.py --print-controls-on-detect
```

### 3. List All Open Top-Level Windows
Use this utility to see all open windows on the Windows desktop along with their Process IDs (PIDs) and class names:
```bash
python main.py --list-windows
```

### 4. Print Controls of the Active Permission Dialog
Use this utility to print the control identifier tree of the currently opened Antigravity permission dialog (if it's on screen):
```bash
python main.py --print-controls
```

---

## Troubleshooting & Best Practices

- **Permissions (Run as Admin)**: If the target application (e.g., Antigravity IDE) runs with Administrator privileges (elevated rights), Windows security policies (UAC) will block standard user accounts from sending input to it. **You must run the terminal or IDE running this script as Administrator** to allow it to inspect or click the dialog.
- **Windows Focus / Sleep Mode**: Windows UI Automation depends on the UI session being active. If your screen is locked or in sleep mode, UIA elements might not be detectable.
- **UI Automation Backend**: This agent uses the standard Microsoft UI Automation framework (the `"uia"` backend in pywinauto). It is highly optimized for modern WPF, Electron, and WinForms applications.
