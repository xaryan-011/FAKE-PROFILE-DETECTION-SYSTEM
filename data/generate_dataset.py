"""
Generate a synthetic dataset of ~2000 social media profiles (fake + real).
Realistic distributions based on real-world patterns.
"""

import pandas as pd
import numpy as np
import random
import string
import os

np.random.seed(42)
random.seed(42)

# --- Real profile name parts ---
FIRST_NAMES = [
    "emma", "liam", "olivia", "noah", "ava", "james", "sophia", "william",
    "isabella", "oliver", "mia", "benjamin", "charlotte", "elijah", "amelia",
    "lucas", "harper", "mason", "evelyn", "logan", "aria", "alexander",
    "chloe", "ethan", "ella", "jacob", "luna", "michael", "avery", "daniel",
    "scarlett", "henry", "madison", "jackson", "layla", "sebastian", "penelope",
    "aiden", "riley", "matthew", "zoey", "samuel", "nora", "david", "lily",
    "joseph", "eleanor", "carter", "hannah", "owen", "stella", "wyatt", "violet",
    "john", "aurora", "jack", "savannah", "luke", "audrey", "jayden", "brooklyn",
    "dylan", "bella", "grayson", "claire", "levi", "skylar", "isaac", "paisley",
    "gabriel", "natalie", "julian", "anna", "luca", "caroline", "leo", "maya",
    "lincoln", "naomi", "jaxon", "elena", "asher", "sarah", "christopher", "aaliyah",
    "joshua", "kennedy", "andrew", "hazel", "theodore", "madelyn", "caleb", "alice",
    "ryan", "piper", "adrian", "ruby"
]

LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis",
    "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson",
    "thomas", "taylor", "moore", "jackson", "martin", "lee", "perez", "thompson",
    "white", "harris", "sanchez", "clark", "ramirez", "lewis", "robinson", "walker",
    "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill", "flores"
]

REAL_BIO_TEMPLATES = [
    "Love {hobby1} and {hobby2} 🌟 | {city} based",
    "{job} | {hobby1} enthusiast | Living my best life ✨",
    "Just a {adj} soul exploring the world 🌍 | {hobby1}",
    "{job} by day, {hobby1} lover by night 🌙",
    "🎓 {school} alum | {job} | {city}",
    "Mom of {n} | {hobby1} | Coffee addict ☕",
    "📍{city} | {hobby1} & {hobby2} | DM for collabs",
    "Living life one {hobby1} at a time 🏔️",
    "{adj} | {hobby1} | {hobby2} | {city} 📍",
    "🎵 Music lover | {job} | {hobby1}",
    "Wanderlust 🌎 | {hobby1} | {hobby2} | {city}",
    "{job} 💼 | Family first ❤️ | {hobby1}",
    "Dreamer & doer ✨ | {hobby1} | {city}",
    "Life is short, eat dessert first 🍰 | {hobby1}",
    "Dog parent 🐕 | {job} | {hobby1} fanatic",
    "Fitness & wellness 💪 | {hobby1} | {city}",
    "Creative mind | {hobby1} | {hobby2} | Let's connect!",
    "📸 {hobby1} | Travel addict | {city} native",
    "Spreading positivity ☀️ | {job} | {hobby1}",
    "Bookworm 📚 | {hobby1} | {hobby2} | Introvert at heart",
]

FAKE_BIO_TEMPLATES = [
    "Click link in bio for FREE money 💰💰💰",
    "DM me for exclusive offers!!!",
    "Follow me I follow back! F4F! 🔥🔥🔥",
    "Make $5000/day working from home! Link below 👇",
    "FREE followers! Click the link NOW!!!",
    "Hot singles in your area 😍 DM NOW",
    "Crypto millionaire 💎🙌 Join my course!",
    "I make $10k/week! Ask me how 💵💵💵",
    "Buy followers cheap! DM for prices!",
    "Free gift cards! Limited time offer! Click NOW!",
    "Want to lose 20lbs fast?? DM me!!!",
    "Invest in crypto NOW! Double your money! 🚀🚀🚀",
    "Adult content 🔞 Link below for more",
    "CHEAP followers and likes! Best prices! DM!!!",
    "Follow 4 Follow! Like 4 Like! 💯💯💯",
    "",
    "",
    "",
    ".",
    "....",
]

HOBBIES = [
    "photography", "hiking", "cooking", "yoga", "reading", "travel",
    "painting", "gaming", "running", "surfing", "cycling", "music",
    "dance", "fitness", "gardening", "camping", "skiing", "writing",
    "baking", "meditation", "skateboarding", "swimming"
]
JOBS = [
    "Software Engineer", "Designer", "Teacher", "Nurse", "Doctor",
    "Photographer", "Writer", "Artist", "Chef", "Entrepreneur",
    "Consultant", "Manager", "Marketing Lead", "Data Analyst",
    "Architect", "Lawyer", "Accountant"
]
CITIES = [
    "NYC", "LA", "San Francisco", "Chicago", "Miami", "Seattle",
    "Austin", "Denver", "Portland", "Boston", "London", "Paris",
    "Tokyo", "Berlin", "Barcelona", "Toronto", "Sydney", "Dubai"
]
ADJECTIVES = ["creative", "passionate", "curious", "adventurous", "ambitious", "chill", "happy"]
SCHOOLS = ["UCLA", "MIT", "Stanford", "NYU", "Harvard", "Berkeley", "Columbia", "Oxford"]


def generate_real_username():
    """Generate a realistic username."""
    patterns = [
        lambda: f"{random.choice(FIRST_NAMES)}.{random.choice(LAST_NAMES)}",
        lambda: f"{random.choice(FIRST_NAMES)}_{random.choice(LAST_NAMES)}",
        lambda: f"{random.choice(FIRST_NAMES)}{random.choice(LAST_NAMES)}{random.randint(1, 99)}",
        lambda: f"{random.choice(FIRST_NAMES)}_{random.randint(90, 99)}",
        lambda: f"the_{random.choice(FIRST_NAMES)}",
        lambda: f"{random.choice(FIRST_NAMES)}{random.choice(LAST_NAMES)}",
        lambda: f"{random.choice(FIRST_NAMES)}.{random.choice(LAST_NAMES)}.official",
    ]
    return random.choice(patterns)()


def generate_fake_username():
    """Generate a suspicious/bot-like username."""
    patterns = [
        lambda: ''.join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(12, 20))),
        lambda: f"user{random.randint(100000, 999999)}",
        lambda: f"{''.join(random.choices(string.ascii_lowercase, k=4))}{random.randint(1000, 9999)}{''.join(random.choices(string.ascii_lowercase, k=3))}",
        lambda: f"free_{''.join(random.choices(string.ascii_lowercase, k=5))}_{random.randint(100, 999)}",
        lambda: f"{''.join(random.choices(string.ascii_lowercase, k=3))}{''.join(random.choices(string.digits, k=8))}",
        lambda: f"follow_me_{''.join(random.choices(string.digits, k=6))}",
        lambda: f"real_{''.join(random.choices(string.ascii_lowercase, k=6))}{''.join(random.choices(string.digits, k=4))}",
        lambda: f"x{''.join(random.choices(string.ascii_lowercase + string.digits, k=15))}",
    ]
    return random.choice(patterns)()


def generate_real_bio():
    """Generate a realistic bio."""
    template = random.choice(REAL_BIO_TEMPLATES)
    return template.format(
        hobby1=random.choice(HOBBIES),
        hobby2=random.choice(HOBBIES),
        city=random.choice(CITIES),
        job=random.choice(JOBS),
        adj=random.choice(ADJECTIVES),
        school=random.choice(SCHOOLS),
        n=random.randint(1, 3),
    )


def generate_fake_bio():
    """Generate a spam/fake bio."""
    return random.choice(FAKE_BIO_TEMPLATES)


def generate_dataset(n_total=2000):
    """Generate a balanced dataset of fake and real profiles."""
    n_fake = n_total // 2
    n_real = n_total - n_fake

    profiles = []

    # --- Generate REAL profiles ---
    for _ in range(n_real):
        age_days = int(np.random.lognormal(mean=6.5, sigma=0.8))
        age_days = min(max(age_days, 30), 5000)
        followers = int(np.random.lognormal(mean=5.5, sigma=1.5))
        followers = min(max(followers, 10), 500000)
        following = int(np.random.lognormal(mean=5.2, sigma=1.0))
        following = min(max(following, 5), 7500)
        posts = int(np.random.lognormal(mean=3.5, sigma=1.2))
        posts = min(max(posts, 1), 5000)

        has_profile_pic = int(np.random.random() < 0.95)
        has_url = int(np.random.random() < 0.30)

        profile = {
            "username": generate_real_username(),
            "bio": generate_real_bio(),
            "followers": followers,
            "following": following,
            "posts": posts,
            "account_age_days": age_days,
            "has_profile_pic": has_profile_pic,
            "has_url": has_url,
            "is_fake": 0,
        }
        profiles.append(profile)

    # --- Generate FAKE profiles ---
    for _ in range(n_fake):
        age_days = int(np.random.exponential(scale=30))
        age_days = min(max(age_days, 1), 365)
        followers = int(np.random.exponential(scale=20))
        followers = min(max(followers, 0), 500)

        # Fake accounts often follow WAY more than they have followers
        following = int(np.random.lognormal(mean=6.0, sigma=1.5))
        following = min(max(following, 50), 7500)

        posts = int(np.random.exponential(scale=3))
        posts = min(max(posts, 0), 20)

        has_profile_pic = int(np.random.random() < 0.35)
        has_url = int(np.random.random() < 0.65)

        profile = {
            "username": generate_fake_username(),
            "bio": generate_fake_bio(),
            "followers": followers,
            "following": following,
            "posts": posts,
            "account_age_days": age_days,
            "has_profile_pic": has_profile_pic,
            "has_url": has_url,
            "is_fake": 1,
        }
        profiles.append(profile)

    # Shuffle
    random.shuffle(profiles)
    df = pd.DataFrame(profiles)
    return df


if __name__ == "__main__":
    df = generate_dataset(2000)
    output_path = os.path.join(os.path.dirname(__file__), "profiles.csv")
    df.to_csv(output_path, index=False)
    print(f"[OK] Generated {len(df)} profiles -> {output_path}")
    print(f"   Real: {(df['is_fake'] == 0).sum()}, Fake: {(df['is_fake'] == 1).sum()}")
    print(f"\nSample:\n{df.head(10).to_string()}")
