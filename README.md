# Antigravity Desktop UI Automation Agent

A cross-platform desktop UI Automation agent built in Python to automatically detect Antigravity permission dialogs (such as command execution prompts or path access requests) and click target action buttons (**Submit**, **Retry**, **Allow**) outside the browser.

Supports both **Microsoft Windows** (via `pywinauto` / Microsoft UI Automation) and **Apple macOS** (via native AppleScript / `System Events` Accessibility API).

---

## Project Structure

```text
antigravity-agent/
├── main.py                 # Cross-platform CLI entry point & OS router
├── mac_agent.py            # macOS desktop automation (AppleScript / System Events)
├── watcher.py              # Windows polling loop & state watcher
├── automation.py           # Windows pywinauto integration (UIA controls & clicking)
├── config.py               # Configuration parameters & matching rules
├── requirements.txt        # Package dependencies (with platform markers)
├── antigravity-extension/  # Optional Chrome Extension (for web environments)
└── README.md               # Project documentation
```

---

## Features

- **Cross-Platform Support**: Auto-detects whether you are running on Windows or macOS.
- **Multi-Button Support**: Automatically detects and clicks **Submit**, **Retry**, or **Allow** buttons (configurable via `config.py` or `--buttons` flag).
- **Flexible Path & Command Dialog Matching**: Matches prompts for running commands as well as file/folder access permissions.
- **Reliable Clicking**: Interacts with the desktop application window directly outside any browser.
- **Prevent Double-Clicking**: Maintains state to ensure it only clicks a specific dialog instance once.
- **Graceful Shutdown**: Intercepts `Ctrl+C` for a clean exit.
- **Diagnostic Utilities**:
  - List all active top-level windows (`--list-windows`).
  - Print the detailed control identifier tree of the permission dialog on Windows (`--print-controls`).

---

## Installation

### 1. Requirements
* Python 3.10 or higher.

### 2. Install Dependencies
Open your terminal (PowerShell on Windows, Terminal on macOS) and run:
```bash
pip install -r requirements.txt
```
*(On macOS, the Windows-specific packages `pywinauto` / `pywin32` / `comtypes` are automatically skipped, so installation completes with zero errors).*

---

## macOS Setup (Important)

On macOS, any script controlling other desktop applications requires **Accessibility permission**:
1. Open **System Settings** on your Mac.
2. Navigate to **Privacy & Security** → **Accessibility**.
3. Add or toggle **ON** the terminal you use (e.g., **Terminal**, **iTerm2**, or **VS Code**).

---

## Usage

### 1. Run the Watcher Agent (Default)
Start the agent to continuously monitor and approve permission dialogs:
```bash
python main.py
```
*(On Windows you can also use `py main.py`)*

*Press `Ctrl+C` at any time to exit the watcher.*

### 2. Run with Custom Target Buttons
Override default target buttons via command line argument:
```bash
python main.py --buttons Submit Retry Allow
```

### 3. List All Open Top-Level Windows
Use this utility to see all open windows along with their Process IDs (PIDs) and titles:
```bash
python main.py --list-windows
```

### 4. Windows Only: Print Controls of the Active Permission Dialog
Print the control identifier tree of the currently opened permission dialog:
```bash
python main.py --print-controls
```

---

## Troubleshooting & Best Practices

- **Windows Administrator Rights**: If Antigravity runs with Administrator privileges, Windows security policies (UAC) block standard user processes from sending clicks to it. Run your terminal as Administrator.
- **macOS Accessibility Rights**: If you see `Error: -1743: Not authorized to send Apple events`, ensure Terminal is enabled in **System Settings → Privacy & Security → Accessibility**.
- **Browser Alternative**: If you use Antigravity in Google Chrome or a Cloud Web IDE, you can also use the included Chrome extension in [`antigravity-extension`](antigravity-extension/).
