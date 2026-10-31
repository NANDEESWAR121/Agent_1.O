// background/service-worker.js
// Antigravity Agent Background Service Worker (Manifest V3)

const DEFAULT_SETTINGS = {
  isWatching: true,
  pollingIntervalMs: 1500,
  targetButtons: ["Submit", "Retry", "Allow"],
  textKeywords: [
    "Allow running this command?",
    "Agent terminated due to error",
    "prompt the model to try again",
    "start a new conversation",
    "access",
    "read path",
    "permission",
    "allow",
    "retry"
  ],
  titleKeywords: [
    "Antigravity",
    "Permission",
    "Confirm",
    "Allow",
    "Security",
    "Agent",
    "Error"
  ],
  stats: {
    clicksCount: 0,
    dialogsDetectedCount: 0,
    lastActionTime: null
  }
};

// Initialize settings on extension install / startup
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(Object.keys(DEFAULT_SETTINGS), (stored) => {
    const toSave = {};
    for (const [key, value] of Object.entries(DEFAULT_SETTINGS)) {
      if (stored[key] === undefined) {
        toSave[key] = value;
      }
    }
    if (Object.keys(toSave).length > 0) {
      chrome.storage.local.set(toSave, () => {
        console.log("[Antigravity Background] Default settings initialized.");
      });
    }
  });
  updateBadge(true);
});

// Update extension icon badge depending on active status
function updateBadge(isWatching) {
  if (isWatching) {
    chrome.action.setBadgeText({ text: "ON" });
    chrome.action.setBadgeBackgroundColor({ color: "#22c55e" }); // Green
  } else {
    chrome.action.setBadgeText({ text: "OFF" });
    chrome.action.setBadgeBackgroundColor({ color: "#64748b" }); // Slate
  }
}

// Handle message requests from Popup and Content Scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_STATE") {
    chrome.storage.local.get(null, (state) => {
      sendResponse({ status: "success", data: state });
    });
    return true; // Async response
  }

  if (message.type === "SET_WATCHER_STATE") {
    const isWatching = Boolean(message.isWatching);
    chrome.storage.local.set({ isWatching }, () => {
      updateBadge(isWatching);
      // Broadcast state change to all open tabs
      chrome.tabs.query({}, (tabs) => {
        for (const tab of tabs) {
          if (tab.id) {
            chrome.tabs.sendMessage(tab.id, { type: "WATCHER_STATE_CHANGED", isWatching }).catch(() => {});
          }
        }
      });
      sendResponse({ status: "success", isWatching });
    });
    return true;
  }

  if (message.type === "RECORD_CLICK") {
    chrome.storage.local.get(["stats"], (result) => {
      const currentStats = result.stats || DEFAULT_SETTINGS.stats;
      const updatedStats = {
        clicksCount: (currentStats.clicksCount || 0) + 1,
        dialogsDetectedCount: (currentStats.dialogsDetectedCount || 0) + 1,
        lastActionTime: new Date().toLocaleTimeString()
      };
      chrome.storage.local.set({ stats: updatedStats }, () => {
        sendResponse({ status: "success", stats: updatedStats });
      });
    });
    return true;
  }
});
