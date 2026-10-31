// options/options.js
// Antigravity Agent Options Page Script

document.addEventListener("DOMContentLoaded", () => {
  const targetButtonsInput = document.getElementById("targetButtonsInput");
  const textKeywordsInput = document.getElementById("textKeywordsInput");
  const pollingIntervalInput = document.getElementById("pollingIntervalInput");
  const saveBtn = document.getElementById("saveBtn");
  const resetBtn = document.getElementById("resetBtn");
  const saveStatus = document.getElementById("saveStatus");

  const DEFAULT_TARGET_BUTTONS = ["Submit", "Retry", "Allow"];
  const DEFAULT_TEXT_KEYWORDS = [
    "Allow running this command?",
    "Agent terminated due to error",
    "prompt the model to try again",
    "start a new conversation",
    "access",
    "read path",
    "permission",
    "allow",
    "retry"
  ];
  const DEFAULT_POLLING_INTERVAL = 1500;

  function loadSettings() {
    chrome.storage.local.get(["targetButtons", "textKeywords", "pollingIntervalMs"], (res) => {
      const targetButtons = res.targetButtons || DEFAULT_TARGET_BUTTONS;
      const textKeywords = res.textKeywords || DEFAULT_TEXT_KEYWORDS;
      const pollingIntervalMs = res.pollingIntervalMs || DEFAULT_POLLING_INTERVAL;

      targetButtonsInput.value = targetButtons.join(", ");
      textKeywordsInput.value = textKeywords.join(", ");
      pollingIntervalInput.value = pollingIntervalMs;
    });
  }

  saveBtn.addEventListener("click", () => {
    const rawButtons = targetButtonsInput.value.split(",").map((s) => s.trim()).filter(Boolean);
    const rawKeywords = textKeywordsInput.value.split(",").map((s) => s.trim()).filter(Boolean);
    const interval = parseInt(pollingIntervalInput.value, 10) || DEFAULT_POLLING_INTERVAL;

    chrome.storage.local.set({
      targetButtons: rawButtons,
      textKeywords: rawKeywords,
      pollingIntervalMs: interval
    }, () => {
      saveStatus.textContent = "✓ Settings saved successfully!";
      setTimeout(() => {
        saveStatus.textContent = "";
      }, 3000);
    });
  });

  resetBtn.addEventListener("click", () => {
    targetButtonsInput.value = DEFAULT_TARGET_BUTTONS.join(", ");
    textKeywordsInput.value = DEFAULT_TEXT_KEYWORDS.join(", ");
    pollingIntervalInput.value = DEFAULT_POLLING_INTERVAL;

    chrome.storage.local.set({
      targetButtons: DEFAULT_TARGET_BUTTONS,
      textKeywords: DEFAULT_TEXT_KEYWORDS,
      pollingIntervalMs: DEFAULT_POLLING_INTERVAL
    }, () => {
      saveStatus.textContent = "✓ Reset to default settings.";
      setTimeout(() => {
        saveStatus.textContent = "";
      }, 3000);
    });
  });

  loadSettings();
});
