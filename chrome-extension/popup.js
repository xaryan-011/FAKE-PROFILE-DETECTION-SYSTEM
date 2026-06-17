const API_URL = 'http://127.0.0.1:8000/api/extension/predict';
const HEALTH_URL = 'http://127.0.0.1:8000/health';

// --- Tab switching ---
document.querySelectorAll('.popup-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.popup-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
    // Reset results when switching tabs
    document.getElementById('result').style.display = 'none';
    document.getElementById('loading').style.display = 'none';
  });
});

// --- Connection check ---
async function checkConnection() {
  const dot = document.getElementById('connection-status');
  try {
    const res = await fetch(HEALTH_URL, { signal: AbortSignal.timeout(2000) });
    if (res.ok) {
      dot.className = 'connection-dot online';
      dot.title = 'Backend connected';
      return true;
    }
  } catch {}
  dot.className = 'connection-dot offline';
  dot.title = 'Backend not reachable';
  return false;
}

// Check on popup open
checkConnection();

// --- Display results ---
function displayResults(result, username) {
  const loadingEl = document.getElementById('loading');
  const resultEl = document.getElementById('result');
  const statusEl = document.getElementById('status');

  loadingEl.style.display = 'none';
  resultEl.style.display = 'block';

  const iconEl = document.getElementById('result-icon');
  const textEl = document.getElementById('result-text');
  const scoreEl = document.getElementById('result-score');
  const reasonsEl = document.getElementById('result-reasons');

  if (result.is_fake) {
    iconEl.textContent = '🚨';
    iconEl.className = 'result-icon danger';
    textEl.textContent = 'LIKELY FAKE';
    textEl.className = 'result-text danger';
  } else {
    iconEl.textContent = '✅';
    iconEl.className = 'result-icon safe';
    textEl.textContent = 'LIKELY REAL';
    textEl.className = 'result-text safe';
  }

  scoreEl.textContent = `Risk Score: ${result.fake_percentage}%`;

  reasonsEl.innerHTML = '';
  if (result.reasons) {
    result.reasons.forEach(reason => {
      const div = document.createElement('div');
      div.className = 'reason-item';
      div.textContent = reason;
      reasonsEl.appendChild(div);
    });
  }

  if (statusEl) {
    statusEl.textContent = `@${username} - Analysis complete`;
  }
}

// --- Auto Scan ---
document.getElementById('scan-btn').addEventListener('click', async () => {
  const statusEl = document.getElementById('status');
  const resultEl = document.getElementById('result');
  const loadingEl = document.getElementById('loading');
  const scanBtn = document.getElementById('scan-btn');

  // Reset
  resultEl.style.display = 'none';
  loadingEl.style.display = 'flex';
  scanBtn.disabled = true;
  statusEl.textContent = 'Checking connection...';
  statusEl.style.color = '';

  // Check backend first
  const connected = await checkConnection();
  if (!connected) {
    loadingEl.style.display = 'none';
    statusEl.textContent = 'Backend not running. Start the server on port 8000.';
    statusEl.style.color = '#ef4444';
    scanBtn.disabled = false;
    return;
  }

  statusEl.textContent = 'Scanning profile...';

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab.url || !tab.url.includes('instagram.com')) {
      throw new Error('Please navigate to an Instagram profile first');
    }

    const profileData = await new Promise((resolve, reject) => {
      chrome.tabs.sendMessage(tab.id, { type: 'GET_PROFILE' }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error('Could not read profile. Please refresh the page and try again.'));
          return;
        }
        if (!response || !response.username) {
          reject(new Error('No profile data found. Make sure you are on a profile page.'));
          return;
        }
        resolve(response);
      });
    });

    statusEl.textContent = `Analyzing @${profileData.username}...`;

    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profileData),
    });

    if (!response.ok) {
      throw new Error('API error. Make sure the backend is running.');
    }

    const result = await response.json();
    displayResults(result, profileData.username);

  } catch (error) {
    loadingEl.style.display = 'none';
    statusEl.textContent = error.message;
    statusEl.style.color = '#ef4444';
  } finally {
    scanBtn.disabled = false;
  }
});

// --- Manual Entry ---
document.getElementById('manual-form').addEventListener('submit', async (e) => {
  e.preventDefault();

  const resultEl = document.getElementById('result');
  const loadingEl = document.getElementById('loading');

  resultEl.style.display = 'none';
  loadingEl.style.display = 'flex';

  const connected = await checkConnection();
  if (!connected) {
    loadingEl.style.display = 'none';
    alert('Backend not running. Start the server on port 8000.');
    return;
  }

  const profileData = {
    username: document.getElementById('m-username').value.trim(),
    bio: document.getElementById('m-bio').value.trim(),
    followers: parseInt(document.getElementById('m-followers').value) || 0,
    following: parseInt(document.getElementById('m-following').value) || 0,
    posts: parseInt(document.getElementById('m-posts').value) || 0,
    account_age_days: parseInt(document.getElementById('m-age').value) || 365,
    has_profile_pic: 1,
    has_url: 0,
  };

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profileData),
    });

    if (!response.ok) {
      throw new Error('API error');
    }

    const result = await response.json();
    displayResults(result, profileData.username);

  } catch (error) {
    loadingEl.style.display = 'none';
    alert('Analysis failed: ' + error.message);
  }
});
