import re
from urllib.parse import urlparse


TRUSTED_DOMAINS = {
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "google.com",
    "docs.google.com",
    "drive.google.com",
    "meet.google.com",
    "youtube.com",
    "youtu.be",
    "linkedin.com",
    "microsoft.com",
    "apple.com",
    "wikipedia.org",
    "stackoverflow.com",
    "npmjs.com",
    "pypi.org",
    "medium.com",
    "notion.so",
    "figma.com",
    "dropbox.com",
    "slack.com",
    "zoom.us",
    "paypal.com",
    "facebook.com",
    "instagram.com",
    "whatsapp.com",
}

# Real domains for brands commonly impersonated in phishing links.
LEGITIMATE_BRAND_DOMAINS = {
    "paypal": {"paypal.com", "www.paypal.com"},
    "facebook": {"facebook.com", "www.facebook.com", "m.facebook.com", "fb.com"},
    "instagram": {"instagram.com", "www.instagram.com"},
    "whatsapp": {"whatsapp.com", "www.whatsapp.com", "web.whatsapp.com"},
    "google": {"google.com", "www.google.com", "accounts.google.com", "docs.google.com"},
    "microsoft": {"microsoft.com", "www.microsoft.com", "login.microsoftonline.com"},
    "apple": {"apple.com", "www.apple.com", "icloud.com"},
    "amazon": {"amazon.com", "www.amazon.com"},
    "sampath": {"sampath.lk", "www.sampath.lk"},
    "commercial": {"combank.lk", "www.combank.lk"},
    "hnb": {"hnb.lk", "www.hnb.lk"},
    "boc": {"boc.lk", "www.boc.lk"},
}


def _normalize_domain(domain):
    domain = domain.lower().strip(".")
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def is_trusted_domain(domain):
    domain = _normalize_domain(domain)
    if domain in TRUSTED_DOMAINS:
        return True
    return any(domain.endswith(f".{trusted}") for trusted in TRUSTED_DOMAINS)


def _detect_brand_impersonation(domain):
    domain = _normalize_domain(domain)
    flags = []

    for brand, legit_domains in LEGITIMATE_BRAND_DOMAINS.items():
        if brand not in domain:
            continue
        if domain in legit_domains or any(domain.endswith(f".{legit}") for legit in legit_domains):
            continue
        flags.append(f"Domain appears to impersonate {brand.title()} (not an official domain)")
        return flags

    return flags


def extract_urls(text):
    """
    Extracts normal URLs and suspicious short/domain-like links.
    """
    url_pattern = r"""
        (
            https?://[^\s]+
            |
            www\.[^\s]+
            |
            [a-zA-Z0-9.-]+\.(?:com|lk|org|net|xyz|top|click|work|loan|tk|ml|df|example|v)(?:/[^\s]*)?
        )
    """

    urls = re.findall(url_pattern, text, re.VERBOSE)

    cleaned_urls = []
    for url in urls:
        cleaned_url = url.strip(".,;:!?)('\"")
        cleaned_urls.append(cleaned_url)

    return cleaned_urls


def analyze_url(url):
    parsed_url = urlparse(url if url.startswith("http") else "http://" + url)
    domain = parsed_url.netloc.lower()
    full_target = f"{domain}{parsed_url.path}".lower()

    if is_trusted_domain(domain):
        return {
            "url": url,
            "url_risk_score": 0,
            "url_risk_factors": ["Known trusted domain"],
            "trusted": True,
        }

    risk_factors = []
    score = 0

    suspicious_tlds = [
        ".xyz", ".top", ".click", ".work", ".loan", ".tk", ".ml", ".df", ".example"
    ]

    shorteners = [
        "bit.ly", "tinyurl.com", "t.co", "goo.gl", "shorturl.at",
        "cutt.ly", "rebrand.ly", "is.gd", "s.id"
    ]

    sensitive_words = [
        "bank", "login", "verify", "secure", "account", "paypal",
        "payment", "otp", "card", "refund", "claim", "parcel",
        "delivery", "update", "reactivate", "security", "review",
    ]

    brand_flags = _detect_brand_impersonation(domain)
    if brand_flags:
        risk_factors.extend(brand_flags)
        score += 45

    if any(tld in domain for tld in suspicious_tlds):
        risk_factors.append("Uses a suspicious or uncommon domain extension")
        score += 25

    if any(shortener in domain for shortener in shorteners):
        risk_factors.append("Uses a shortened URL that hides the real destination")
        score += 25

    if re.search(r"\d+\.\d+\.\d+\.\d+", domain):
        risk_factors.append("Uses an IP address instead of a normal domain name")
        score += 25

    hyphen_count = domain.count("-")
    if hyphen_count >= 2:
        risk_factors.append("Domain contains multiple hyphens, common in phishing sites")
        score += 20
    elif hyphen_count == 1:
        risk_factors.append("Domain contains hyphens, which are common in fake websites")
        score += 10

    if len(domain) > 30:
        risk_factors.append("Domain name is unusually long")
        score += 10

    sensitive_hits = [word for word in sensitive_words if word in full_target]
    if len(sensitive_hits) >= 2:
        risk_factors.append(
            "URL contains multiple sensitive words: " + ", ".join(sensitive_hits[:4])
        )
        score += 35
    elif len(sensitive_hits) == 1:
        risk_factors.append(
            f"URL contains sensitive scam-related word: {sensitive_hits[0]}"
        )
        score += 20

    if parsed_url.scheme == "http":
        risk_factors.append("Uses HTTP instead of HTTPS")
        score += 10

    if not risk_factors:
        risk_factors.append("No major suspicious URL indicators detected")

    score = min(score, 100)

    return {
        "url": url,
        "url_risk_score": score,
        "url_risk_factors": risk_factors,
        "trusted": False,
    }


def analyze_urls_in_message(message):
    urls = extract_urls(message)

    if not urls:
        return []

    return [analyze_url(url) for url in urls]
