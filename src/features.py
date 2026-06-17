"""
Feature engineering module for fake profile detection.
Extracts numeric features from raw profile data.
"""

import math
import re
from collections import Counter

# Spam keywords commonly found in fake bios
SPAM_KEYWORDS = [
    "free", "click", "link", "follow", "money", "earn", "profit",
    "offer", "dm", "buy", "cheap", "discount", "winner", "prize",
    "invest", "crypto", "bitcoin", "forex", "trading", "income",
    "cash", "dollar", "rich", "wealth", "luxury", "exclusive",
    "limited", "hurry", "fast", "double", "triple", "guaranteed",
    "100%", "amazing", "incredible", "unbelievable", "secret",
    "hack", "trick", "method", "system", "auto", "bot",
    "followers", "likes", "f4f", "l4l", "s4s", "adult", "hot",
    "singles", "dating", "18+", "nude", "xxx",
]

# Sentiment word lists for bio analysis
POSITIVE_WORDS = {
    "love", "like", "explore", "enthusiast", "creative", "passionate", "curious", 
    "adventurous", "ambitious", "happy", "smile", "art", "music", "family", "parent",
    "photographer", "developer", "engineer", "designer", "teacher", "doctor", "writer",
    "living", "best", "dreamer", "doer", "positivity", "blessed", "travel", "hiking",
    "coffee", "fitness", "wellness", "nature", "peace", "student", "learning"
}
SPAM_WORDS = {
    "free", "click", "link", "money", "earn", "profit", "offer", "dm", "buy", 
    "cheap", "discount", "winner", "prize", "invest", "crypto", "bitcoin", "forex", 
    "trading", "income", "cash", "rich", "wealth", "luxury", "limited", "hurry", 
    "guaranteed", "hack", "bot", "followers", "likes", "nude", "xxx", "hot", "dating",
    "double", "triple", "cashout", "100%", "f4f", "l4l"
}


def calculate_entropy(text):
    """Calculate Shannon entropy of a string — measures randomness."""
    if not text:
        return 0.0
    counter = Counter(text.lower())
    length = len(text)
    entropy = -sum(
        (count / length) * math.log2(count / length)
        for count in counter.values()
    )
    return round(entropy, 4)


def count_spam_keywords(text):
    """Count how many spam keywords appear in the text."""
    if not text:
        return 0
    text_lower = text.lower()
    return sum(1 for keyword in SPAM_KEYWORDS if keyword in text_lower)


def digit_ratio(text):
    """Ratio of digits to total characters."""
    if not text:
        return 0.0
    digits = sum(1 for c in text if c.isdigit())
    return round(digits / len(text), 4)


def special_char_count(text):
    """Count non-alphanumeric, non-space characters."""
    if not text:
        return 0
    return sum(1 for c in text if not c.isalnum() and c != ' ')


def repetition_score(text):
    """Detect repeated characters/patterns. Higher = more repetitive."""
    if not text or len(text) < 3:
        return 0.0
    # Count consecutive repeated chars
    repeats = 0
    for i in range(1, len(text)):
        if text[i] == text[i - 1]:
            repeats += 1
    return round(repeats / len(text), 4)


def max_consecutive_digits(text):
    """Find the length of the longest consecutive run of digits."""
    if not text:
        return 0
    runs = re.findall(r'\d+', text)
    if not runs:
        return 0
    return max(len(run) for run in runs)


def bio_uppercase_ratio(text):
    """Proportion of uppercase letters relative to total letters in bio."""
    if not text:
        return 0.0
    letters = sum(1 for c in text if c.isalpha())
    if letters == 0:
        return 0.0
    uppers = sum(1 for c in text if c.isupper())
    return round(uppers / letters, 4)


def count_emojis(text):
    """Count emoji symbols using Unicode range filters."""
    if not text:
        return 0
    emoji_count = 0
    for char in text:
        if 0x1F300 <= ord(char) <= 0x1F9FF or 0x2600 <= ord(char) <= 0x27BF:
            emoji_count += 1
    return emoji_count


def count_links(text):
    """Count explicit and implicit URLs or bio links."""
    if not text:
        return 0
    text_lower = text.lower()
    count = 0
    # Count URLs matching pattern
    count += len(re.findall(r'https?://\S+|www\.\S+', text_lower))
    # Count other links
    for domain in ['.com/', '.net/', '.org/', 'linktr.ee', 'bit.ly', 'bio.link', 'linkin.bio']:
        if domain in text_lower and not ('https://' in text_lower or 'http://' in text_lower or 'www.' in text_lower):
            count += text_lower.count(domain)
    return count


def calculate_bio_sentiment(text):
    """Estimate sentiment of a bio (-1.0 to 1.0) based on real vs spam lexical hits."""
    if not text:
        return 0.0
    text_lower = text.lower()
    words = re.findall(r'\b[a-z]{3,15}\b', text_lower)
    if not words:
        return 0.0
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    spam_count = sum(1 for w in words if w in SPAM_WORDS)
    
    total = pos_count + spam_count
    if total == 0:
        return 0.0
    return round((pos_count - spam_count) / total, 4)


def extract_features(profile):
    """
    Extract all numeric features from a profile dictionary (30 features total).
    
    Args:
        profile: dict with keys: username, bio, followers, following, 
                 posts, account_age_days, has_profile_pic, has_url
    
    Returns:
        dict of feature_name -> feature_value
    """
    username = str(profile.get("username", ""))
    bio = str(profile.get("bio", ""))
    followers = int(profile.get("followers", 0))
    following = int(profile.get("following", 0))
    posts = int(profile.get("posts", 0))
    age_days = int(profile.get("account_age_days", profile.get("age_days", 1)))
    has_profile_pic = int(profile.get("has_profile_pic", 1))
    has_url = int(profile.get("has_url", 0))

    features = {
        # --- Username features ---
        "username_length": len(username),
        "username_digit_ratio": digit_ratio(username),
        "username_entropy": calculate_entropy(username),
        "username_has_numbers": int(any(c.isdigit() for c in username)),
        "username_special_chars": special_char_count(username),
        "username_consecutive_digits": max_consecutive_digits(username),

        # --- Bio features ---
        "bio_length": len(bio),
        "bio_spam_keyword_count": count_spam_keywords(bio),
        "bio_entropy": calculate_entropy(bio),
        "bio_special_chars": special_char_count(bio),
        "bio_repetition_score": repetition_score(bio),
        "bio_exclamation_count": bio.count("!"),
        "bio_is_empty": int(len(bio.strip()) == 0),
        "bio_uppercase_ratio": bio_uppercase_ratio(bio),
        "bio_emoji_count": count_emojis(bio),
        "bio_link_count": count_links(bio),
        "bio_sentiment_score": calculate_bio_sentiment(bio),

        # --- Activity features ---
        "followers": followers,
        "following": following,
        "posts": posts,
        "account_age_days": age_days,
        "followers_following_ratio": round(followers / (following + 1), 4),
        "posts_per_day": round(posts / (age_days + 1), 4),
        "followers_to_following_diff": followers - following,

        # --- Profile features ---
        "has_profile_pic": has_profile_pic,
        "has_url": has_url,

        # --- Derived features ---
        "following_much_more_than_followers": int(following > followers * 5),
        "very_new_account": int(age_days < 30),
        "zero_posts": int(posts == 0),
        "high_follow_count": int(following > 1000),
    }

    return features


# Ordered list of feature names (for model input)
FEATURE_NAMES = [
    "username_length", "username_digit_ratio", "username_entropy",
    "username_has_numbers", "username_special_chars", "username_consecutive_digits",
    "bio_length", "bio_spam_keyword_count", "bio_entropy",
    "bio_special_chars", "bio_repetition_score", "bio_exclamation_count",
    "bio_is_empty", "bio_uppercase_ratio", "bio_emoji_count", "bio_link_count",
    "bio_sentiment_score",
    "followers", "following", "posts", "account_age_days",
    "followers_following_ratio", "posts_per_day", "followers_to_following_diff",
    "has_profile_pic", "has_url",
    "following_much_more_than_followers", "very_new_account",
    "zero_posts", "high_follow_count",
]


def profile_to_feature_vector(profile):
    """Convert a profile dict to an ordered feature vector."""
    features = extract_features(profile)
    return [features[name] for name in FEATURE_NAMES]
