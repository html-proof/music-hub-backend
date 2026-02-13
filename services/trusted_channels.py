"""
Trusted Channels — curated list for quality filtering.
"""

# Major global music labels & channels
TRUSTED_MUSIC_CHANNELS = [
    # Global Major Labels
    "Universal Music", "Sony Music", "Warner Music", "Atlantic Records",
    "Republic Records", "Interscope Records", "Columbia Records",
    "RCA Records", "Def Jam Recordings", "Capitol Records",
    "Island Records", "Parlophone Records", "Epic Records",

    # Popular Artist Channels (VEVO etc)
    "VEVO",

    # Indian Music Labels
    "T-Series", "Zee Music Company", "Sony Music India", "YRF",
    "Saregama", "Tips Official", "Speed Records", "Desi Music Factory",
    "Eros Now Music", "Gaana", "JioSaavn", "Shemaroo",
    "Aditya Music", "Lahari Music", "Mango Music", "Sun Music",
    "Think Music", "Sony Music South",

    # K-pop / East Asian
    "HYBE LABELS", "SM Entertainment", "JYP Entertainment",
    "YG Entertainment", "Starship Entertainment", "BANGTANTV",
    "BLACKPINK", "1theK", "Stone Music Entertainment",

    # Electronic / EDM
    "Monstercat", "NCS", "Trap Nation", "MrSuicideSheep",
    "Proximity", "Spinnin Records", "Armada Music",
    "Ultra Music", "Dim Mak Records", "OWSLA",
    "Revealed Recordings", "Musical Freedom",

    # Independent / Other
    "NPR Music", "COLORS", "Genius", "Lyrical Lemonade",
    "WorldStarHipHop", "Mass Appeal", "Majestic Casual",
    "The Vibe Guide", "Selected.", "MrRevillz",
]


def is_trusted_channel(channel_name: str) -> bool:
    """Check if a channel name matches any trusted channel."""
    if not channel_name:
        return False
    channel_lower = channel_name.lower()
    return any(trusted.lower() in channel_lower for trusted in TRUSTED_MUSIC_CHANNELS)


def get_trusted_channel_stats() -> dict:
    """Get stats about trusted channels."""
    return {
        "total_trusted": len(TRUSTED_MUSIC_CHANNELS),
        "global_labels": 13,
        "indian_labels": 12,
        "east_asian_labels": 9,
        "regional_labels": 12,
    }
