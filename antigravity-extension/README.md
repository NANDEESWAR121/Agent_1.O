# Antigravity Agent — Free Chrome Extension

Automated web permission dialog detector and action submitter for Antigravity web environments and Web IDEs.

## Features
- **100% Free**: No license key, device activation, or backend license server required.
- **Manifest V3 Compliant**: Uses modern background service workers, content scripts, and Chrome storage APIs.
- **Instant MutationObserver**: Detects dialogs dynamically injected into web pages in real-time.
- **Customizable**: Configure target buttons ("Submit", "Retry", "Allow") and dialog keywords via the extension options page.
- **Non-Intrusive**: Simulates natural pointer and keyboard DOM events directly inside target pages.

## Installation & Local Testing

1. Open Google Chrome and navigate to `chrome://extensions`.
2. Toggle **Developer mode** on in the top-right corner.
3. Click **Load unpacked**.
4. Select the `antigravity-extension` directory (`e:\Antigravity-agent\antigravity-extension`).
5. The **Antigravity Agent** extension icon will appear in your Chrome toolbar with status **ON**.
6. Open any target website or web app, open the extension popup, and verify real-time monitoring and button clicking.

## Architecture

- `manifest.json`: Extension manifest configuration (Manifest V3).
- `background/service-worker.js`: Central state & stats management.
- `content/content.js`: Real-time DOM MutationObserver & action trigger.
- `popup/`: Sleek dark-mode user control interface.
- `options/`: Customization panel for keywords and polling settings.
