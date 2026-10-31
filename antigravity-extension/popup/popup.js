// popup/popup.js
// Antigravity Agent Popup Logic

document.addEventListener("DOMContentLoaded", () => {
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const clickCountEl = document.getElementById("clickCount");
  const lastActionTimeEl = document.getElementById("lastActionTime");
  const toggleBtn = document.getElementById("toggleBtn");
  const openOptionsBtn = document.getElementById("openOptionsBtn");

  let isWatching = true;

  function updateUI(state) {
    if (!state) return;

    isWatching = state.isWatching !== undefined ? state.isWatching : true;

    if (isWatching) {
      statusDot.className = "dot active";
      statusText.textContent = "Status: Running";
      toggleBtn.textContent = "Stop Agent";
      toggleBtn.className = "primary-btn btn-active";
    } else {
      statusDot.className = "dot";
      statusText.textContent = "Status: Stopped";
      toggleBtn.textContent = "Start Agent";
      toggleBtn.className = "primary-btn btn-stopped";
    }

    if (state.stats) {
      clickCountEl.textContent = state.stats.clicksCount || 0;
      lastActionTimeEl.textContent = state.stats.lastActionTime || "None";
    }
  }

  // Fetch initial state
  chrome.runtime.sendMessage({ type: "GET_STATE" }, (response) => {
    if (response && response.data) {
      updateUI(response.data);
    }
  });

  // Listen for storage changes
  chrome.storage.onChanged.addListener((changes) => {
    chrome.runtime.sendMessage({ type: "GET_STATE" }, (response) => {
      if (response && response.data) {
        updateUI(response.data);
      }
    });
  });

  // Toggle button handler
  toggleBtn.addEventListener("click", () => {
    const nextState = !isWatching;
    chrome.runtime.sendMessage({
      type: "SET_WATCHER_STATE",
      isWatching: nextState
    }, (res) => {
      if (res && res.status === "success") {
        isWatching = nextState;
        updateUI({ isWatching: nextState });
      }
    });
  });

  // Open Options Page
  openOptionsBtn.addEventListener("click", (e) => {
    e.preventDefault();
    if (chrome.runtime.openOptionsPage) {
      chrome.runtime.openOptionsPage();
    } else {
      window.open(chrome.runtime.getURL("options/options.html"));
    }
  });
});
