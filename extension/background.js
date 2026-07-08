chrome.runtime.onInstalled.addListener(() => {
  console.log('Phishing Detector installed.');
  chrome.storage.local.set({
    totalScanned: 0,
    totalThreats: 0,
    scanHistory: []
  });
});

const BACKEND = 'http://127.0.0.1:5000';

// Proxy /predict requests to bypass Mixed Content blocks in Gmail (HTTPS to HTTP)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'predict') {
    fetch(`${BACKEND}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: request.url })
    })
      .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
      })
      .then(data => sendResponse({ success: true, data }))
      .catch(err => sendResponse({ success: false, error: err.message }));

    return true; // Keep message channel open for asynchronous sendResponse
  }
});