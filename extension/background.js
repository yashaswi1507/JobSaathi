// JobSaathi AI — Background Service Worker
// Opens side panel when extension icon is clicked

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

chrome.action.onClicked.addListener(async (tab) => {
  await chrome.sidePanel.open({ tabId: tab.id });
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'jobDetected') {
    // Store job data for sidepanel to pick up
    chrome.storage.local.set({ latestJob: msg.data });
  }
  return true;
});
