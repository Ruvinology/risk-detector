import re
from urllib.parse import urlparse


def extract_urls(text):
    """
    Extracts normal URLs and suspicious short/domain-like links.
    Examples:
    - https://example.com
    - http://example.com
    - www.example.com
    - secure-bank-login.xyz
    - parcel-release.click
    - s.Eds/3Df
    """

    url_pattern = r"""
        (
            https?://[^\s]+
            |
            www\.[^\s]+
            |
            [a-zA-Z0-9.-]+\.(?:com|lk|org|net|xyz|top|click|work|loan|tk|ml|df|v)(?:/[^\s]*)?
        )
    """

    urls = re.findall(url_pattern, text, re.VERBOSE)

    # Remove punctuation often attached at the end of links
    cleaned_urls = []
    for url in urls:
        cleaned_url = url.strip(".,;:!?)('\"")
        cleaned_urls.append(cleaned_url)

    return cleaned_urls


def analyze_url(url):
    parsed_url = urlparse(url if url.startswith("http") else "http://" + url)
    domain = parsed_url.netloc.lower()

    risk_factors = []
    score = 0

    suspicious_tlds = [
        ".xyz", ".top", ".click", ".work", ".loan", ".tk", ".ml", ".df"
    ]

    shorteners = [
        "bit.ly", "tinyurl.com", "t.co", "goo.gl", "shorturl.at",
        "cutt.ly", "rebrand.ly", "is.gd", "s.id"
    ]

    sensitive_words = [
        "bank", "login", "verify", "secure", "account", "paypal",
        "payment", "otp", "card", "refund", "claim", "parcel",
        "delivery", "update", "reactivate"
    ]

    if any(tld in domain for tld in suspicious_tlds):
        risk_factors.append("Uses a suspicious or uncommon domain extension")
        score += 25

    if any(shortener in domain for shortener in shorteners):
        risk_factors.append("Uses a shortened URL that hides the real destination")
        score += 25

    if re.search(r"\d+\.\d+\.\d+\.\d+", domain):
        risk_factors.append("Uses an IP address instead of a normal domain name")
        score += 25

    if "-" in domain:
        risk_factors.append("Domain contains hyphens, which are common in fake websites")
        score += 10

    if len(domain) > 30:
        risk_factors.append("Domain name is unusually long")
        score += 10

    if any(word in url.lower() for word in sensitive_words):
        risk_factors.append("URL contains sensitive scam-related words such as bank, login, verify, parcel, payment, or account")
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
        "url_risk_factors": risk_factors
    }


def analyze_urls_in_message(message):
    urls = extract_urls(message)

    if not urls:
        return []

    return [analyze_url(url) for url in urls]