// content/content.js
// Antigravity Agent Content Script for DOM Dialog Detection & Auto-Clicking

(function () {
  let isWatching = true;
  let targetButtons = ["Submit", "Retry", "Allow"];
  let textKeywords = ["Allow running this command?", "Agent terminated due to error", "permission", "retry"];
  let pollingIntervalMs = 1500;
  let observer = null;
  let pollTimer = null;

  // WeakSet to avoid re-clicking the exact same button element repeatedly
  const processedButtons = new WeakSet();

  // Load configuration from chrome.storage.local
  function loadConfigAndStart() {
    chrome.storage.local.get(
      ["isWatching", "targetButtons", "textKeywords", "pollingIntervalMs"],
      (res) => {
        if (res.isWatching !== undefined) isWatching = res.isWatching;
        if (res.targetButtons) targetButtons = res.targetButtons;
        if (res.textKeywords) textKeywords = res.textKeywords;
        if (res.pollingIntervalMs) pollingIntervalMs = res.pollingIntervalMs;

        if (isWatching) {
          startMonitoring();
        }
      }
    );
  }

  // Listen for real-time state updates from service worker or popup
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === "WATCHER_STATE_CHANGED") {
      isWatching = message.isWatching;
      if (isWatching) {
        startMonitoring();
      } else {
        stopMonitoring();
      }
    }
  });

  function startMonitoring() {
    if (observer) observer.disconnect();
    if (pollTimer) clearInterval(pollTimer);

    console.log("[Antigravity Agent] Content Script watcher active.");

    // Strategy 1: DOM MutationObserver for instant detection
    observer = new MutationObserver(() => {
      if (isWatching) {
        scanAndClick();
      }
    });

    observer.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true,
      attributes: false
    });

    // Strategy 2: Periodic fallback interval scan
    pollTimer = setInterval(() => {
      if (isWatching) {
        scanAndClick();
      }
    }, pollingIntervalMs);

    // Initial scan
    scanAndClick();
  }

  function stopMonitoring() {
    if (observer) {
      observer.disconnect();
      observer = null;
    }
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
    console.log("[Antigravity Agent] Content Script watcher stopped.");
  }

  // Helper to safely extract text content from DOM element
  function getCleanText(el) {
    if (!el) return "";
    return (el.textContent || el.innerText || "").trim().toLowerCase();
  }

  // Helper to check if an element is visible on screen
  function isVisible(el) {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return false;
    const style = window.getComputedStyle(el);
    return style.visibility !== "hidden" && style.display !== "none" && style.opacity !== "0";
  }

  // Main scan and click function
  function scanAndClick() {
    if (!isWatching) return;

    // Collect candidate button / clickable elements across normal DOM & Shadow DOM
    const selectors = [
      "button",
      "a[role='button']",
      "input[type='button']",
      "input[type='submit']",
      "[role='button']",
      ".btn",
      ".button"
    ];

    const candidates = Array.from(document.querySelectorAll(selectors.join(",")));

    for (const btn of candidates) {
      if (processedButtons.has(btn) || !isVisible(btn)) continue;

      const btnText = getCleanText(btn);
      if (!btnText) continue;

      // Check if button text matches any target button keywords
      const matchedTarget = targetButtons.find((target) => {
        const t = target.toLowerCase();
        return btnText === t || btnText.includes(t);
      });

      if (matchedTarget) {
        // Perform non-intrusive DOM click sequence
        executeClick(btn, matchedTarget);
      }
    }
  }

  function executeClick(el, targetName) {
    try {
      processedButtons.add(el);

      console.log(`[Antigravity Agent] Permission/action button found: "${targetName}". Executing click...`);

      // Dispatch realistic mouse events for SPAs / Frameworks (React, Vue, WebComponents)
      const mouseEvents = ["pointerdown", "mousedown", "pointerup", "mouseup", "click"];
      for (const eventName of mouseEvents) {
        const event = new MouseEvent(eventName, {
          bubbles: true,
          cancelable: true,
          view: window
        });
        el.dispatchEvent(event);
      }

      // Also trigger native .click() if available
      if (typeof el.click === "function") {
        el.click();
      }

      // Notify background script to record activity
      chrome.runtime.sendMessage({
        type: "RECORD_CLICK",
        target: targetName,
        timestamp: new Date().toISOString()
      }).catch(() => {});

    } catch (err) {
      console.error("[Antigravity Agent] Error clicking target element:", err);
    }
  }

  // Initialize on page load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadConfigAndStart);
  } else {
    loadConfigAndStart();
  }
})();
