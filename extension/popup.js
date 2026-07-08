chrome.storage.local.get(['totalScanned','totalThreats','totalLinks'], (data) => {
  document.getElementById('scanned').textContent = data.totalScanned || 0;
  document.getElementById('threats').textContent = data.totalThreats || 0;
  document.getElementById('links').textContent = data.totalLinks || 0;
});

// Check if backend is running
fetch('https://email-phishing-detector-cmpz.onrender.com/health')
  .then(r => r.json())
  .then(() => {
    document.getElementById('backendDot').className = 'status-dot dot-green';
    document.getElementById('backendStatus').textContent = 'ML Backend connected';
  })
  .catch(() => {
    document.getElementById('backendDot').className = 'status-dot dot-red';
    document.getElementById('backendStatus').textContent = 'Backend offline — start API';
  });