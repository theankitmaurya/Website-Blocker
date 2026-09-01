"""Domain normalization and validation utilities."""
import re
from urllib.parse import urlparse

# RFC 1123 compliant domain regex
# Labels: 1-63 alphanumeric characters, can contain hyphens in the middle
# Must contain at least one dot and a valid TLD of at least 2 alpha characters
DOMAIN_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$"
)

# IPv4 regex (optional support for direct IP blocking)
IPV4_REGEX = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
)


def normalize_domain(raw_input: str) -> str | None:
    """
    Normalizes a URL or domain string into a clean, canonical domain name.
    
    Examples:
        'https://www.youtube.com/watch?v=123' -> 'youtube.com'
        'http://reddit.com/r/python'          -> 'reddit.com'
        'www.facebook.com'                    -> 'facebook.com'
        'Netflix.com/'                        -> 'netflix.com'
        'invalid url://'                      -> None
        'hello world'                         -> None
    """
    if not raw_input or not isinstance(raw_input, str):
        return None

    cleaned = raw_input.strip()
    if not cleaned:
        return None

    # Disallow whitespace in input
    if any(char.isspace() for char in cleaned):
        return None

    # If scheme is missing, urlparse might place the domain in path
    if "://" not in cleaned:
        # Check if it starts with //
        if cleaned.startswith("//"):
            parsed = urlparse(cleaned)
        else:
            parsed = urlparse(f"http://{cleaned}")
    else:
        parsed = urlparse(cleaned)

    # Extract hostname / netloc
    hostname = parsed.hostname
    if not hostname:
        # Fallback if urlparse failed
        hostname = parsed.path.split("/")[0].split(":")[0]

    if not hostname:
        return None

    hostname = hostname.lower().strip()

    # Strip port if present
    if ":" in hostname:
        hostname = hostname.split(":")[0]

    # Strip leading 'www.' if present
    if hostname.startswith("www."):
        hostname = hostname[4:]

    # Remove trailing dots
    hostname = hostname.rstrip(".")

    if not hostname:
        return None

    if not is_valid_domain(hostname):
        return None

    return hostname


def is_valid_domain(domain: str) -> bool:
    """
    Validates whether the given string is a valid domain or IPv4 address.
    """
    if not domain or not isinstance(domain, str):
        return False

    domain = domain.strip().lower()

    if len(domain) > 253:
        return False

    # Check against standard domain regex
    if DOMAIN_REGEX.match(domain):
        # Ensure no label starts or ends with hyphen
        labels = domain.split(".")
        for label in labels:
            if not label or len(label) > 63 or label.startswith("-") or label.endswith("-"):
                return False
        return True

    # Check if it is a valid IPv4
    if IPV4_REGEX.match(domain):
        return True

    return False


# Known domain to friendly brand name mappings
POPULAR_WEBSITE_NAMES = {
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "reddit.com": "Reddit",
    "instagram.com": "Instagram",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "twitter.com": "Twitter",
    "x.com": "X (Twitter)",
    "netflix.com": "Netflix",
    "tiktok.com": "TikTok",
    "twitch.tv": "Twitch",
    "twitch.com": "Twitch",
    "github.com": "GitHub",
    "gitlab.com": "GitLab",
    "discord.com": "Discord",
    "discord.gg": "Discord",
    "linkedin.com": "LinkedIn",
    "amazon.com": "Amazon",
    "pinterest.com": "Pinterest",
    "quora.com": "Quora",
    "wikipedia.org": "Wikipedia",
    "spotify.com": "Spotify",
    "whatsapp.com": "WhatsApp",
    "telegram.org": "Telegram",
    "t.me": "Telegram",
    "hulu.com": "Hulu",
    "disneyplus.com": "Disney+",
    "primevideo.com": "Prime Video",
    "chatgpt.com": "ChatGPT",
    "openai.com": "OpenAI",
    "claude.ai": "Claude",
    "medium.com": "Medium",
    "stackoverflow.com": "Stack Overflow",
    "stackexchange.com": "Stack Exchange",
    "steamcommunity.com": "Steam",
    "steampowered.com": "Steam",
    "roblox.com": "Roblox",
    "epicgames.com": "Epic Games",
    "cnn.com": "CNN",
    "bbc.com": "BBC",
    "bbc.co.uk": "BBC",
    "nytimes.com": "The New York Times",
    "wsj.com": "The Wall Street Journal",
    "theverge.com": "The Verge",
    "techcrunch.com": "TechCrunch",
    "news.ycombinator.com": "Hacker News",
    "ycombinator.com": "Y Combinator",
    "ebay.com": "eBay",
    "apple.com": "Apple",
    "google.com": "Google",
    "microsoft.com": "Microsoft",
    "yahoo.com": "Yahoo",
    "bing.com": "Bing",
    "duckduckgo.com": "DuckDuckGo",
    "zoom.us": "Zoom",
    "slack.com": "Slack",
    "notion.so": "Notion",
    "trello.com": "Trello",
    "figma.com": "Figma",
    "canva.com": "Canva",
    "threads.net": "Threads",
    "snapchat.com": "Snapchat",
    "tumblr.com": "Tumblr",
    "vimeo.com": "Vimeo",
    "soundcloud.com": "SoundCloud",
    "coursera.org": "Coursera",
    "udemy.com": "Udemy",
    "imdb.com": "IMDb",
    "khanacademy.org": "Khan Academy",
    "duolingo.com": "Duolingo",
}

MULTI_PART_TLDS = {
    "co.uk", "gov.uk", "ac.uk", "org.uk", "net.uk",
    "co.in", "net.in", "org.in", "gov.in",
    "co.jp", "ne.jp", "ac.jp", "go.jp",
    "com.au", "net.au", "org.au", "edu.au",
    "com.br", "org.br", "net.br",
    "co.nz", "org.nz", "net.nz",
    "co.za", "org.za", "net.za",
    "com.sg", "edu.sg",
}


def get_website_name(raw_input_or_domain: str) -> str:
    """
    Extracts a clean, human-readable website brand name from a URL or domain.
    
    Examples:
        'https://www.youtube.com/watch?v=123' -> 'YouTube'
        'reddit.com'                          -> 'Reddit'
        'news.ycombinator.com'                -> 'Hacker News'
        'my-cool-blog.io'                     -> 'My Cool Blog'
        '192.168.1.1'                         -> '192.168.1.1'
    """
    if not raw_input_or_domain or not isinstance(raw_input_or_domain, str):
        return ""

    domain = normalize_domain(raw_input_or_domain) or raw_input_or_domain.strip().lower()
    if not domain:
        return ""

    # Check popular database
    if domain in POPULAR_WEBSITE_NAMES:
        return POPULAR_WEBSITE_NAMES[domain]

    # Direct IPv4 check
    if IPV4_REGEX.match(domain):
        return domain

    # Strip known multi-part TLD or regular TLD
    parts = domain.split(".")
    if len(parts) >= 2:
        two_part_tld = ".".join(parts[-2:])
        if two_part_tld in MULTI_PART_TLDS:
            labels = parts[:-2]
        else:
            labels = parts[:-1]
    else:
        labels = parts

    if not labels:
        labels = [domain]

    main_name = labels[-1]

    # Convert hyphens/underscores to spaces and title-case
    words = re.split(r"[-_]+", main_name)
    title_cased = " ".join(word.capitalize() for word in words if word)

    return title_cased or domain.capitalize()

