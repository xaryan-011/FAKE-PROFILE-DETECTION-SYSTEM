/**
 * Content script injected into Instagram pages.
 * Scrapes visible profile data from the current page.
 */

function getProfileData() {
  try {
    // Get username from the page header
    const usernameEl = document.querySelector('header h2') || 
                       document.querySelector('header span[dir="auto"]') ||
                       document.querySelector('h2');
    const username = usernameEl ? usernameEl.innerText.trim() : '';

    // Get bio
    const bioEl = document.querySelector('header section > div:last-child > div > span') ||
                  document.querySelector('div[data-testid="user-bio"]') ||
                  document.querySelector('header div > span');
    const bio = bioEl ? bioEl.innerText.trim() : '';

    // Get stats (posts, followers, following)
    const statElements = document.querySelectorAll('header section ul li span, header section ul li a span');
    let posts = 0, followers = 0, following = 0;
    
    if (statElements.length >= 3) {
      posts = parseStatNumber(statElements[0]?.innerText || '0');
      followers = parseStatNumber(statElements[1]?.innerText || '0');
      following = parseStatNumber(statElements[2]?.innerText || '0');
    }

    // Check for profile picture (non-default)
    const profilePicEl = document.querySelector('header img[alt*="profile"]') || 
                        document.querySelector('header canvas');
    const hasProfilePic = profilePicEl ? 1 : 0;

    // Check for external URL
    const urlEl = document.querySelector('header a[rel="me nofollow noopener noreferrer"]') ||
                  document.querySelector('header div a[href*="l.instagram.com"]');
    const hasUrl = urlEl ? 1 : 0;

    return {
      username,
      bio,
      followers,
      following,
      posts,
      account_age_days: 100, // Instagram doesn't expose this; placeholder
      has_profile_pic: hasProfilePic,
      has_url: hasUrl,
    };
  } catch (error) {
    console.error('[ShieldAI] Error scraping profile:', error);
    return null;
  }
}

function parseStatNumber(text) {
  if (!text) return 0;
  text = text.replace(/,/g, '').trim();
  
  if (text.includes('K') || text.includes('k')) {
    return Math.round(parseFloat(text) * 1000);
  }
  if (text.includes('M') || text.includes('m')) {
    return Math.round(parseFloat(text) * 1000000);
  }
  
  return parseInt(text) || 0;
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'GET_PROFILE') {
    const data = getProfileData();
    sendResponse(data);
  }
  return true; // Keep message channel open for async response
});
