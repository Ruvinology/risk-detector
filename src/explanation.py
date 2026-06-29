import re


def contains_phrase(message_lower, phrase):
    """
    Match whole words/phrases to avoid false positives such as
    'rs' matching inside a username or domain name.
    """
    phrase = phrase.lower().strip()

    if phrase == "rs." or phrase == "rs":
        return bool(re.search(r"\brs\.?\b", message_lower))

    if " " in phrase or len(phrase) > 4:
        return phrase in message_lower

    return bool(re.search(rf"(?:^|\W){re.escape(phrase)}(?:\W|$)", message_lower))


def contains_any(message_lower, keyword_list):
    """
    Checks whether any keyword or phrase exists in the message.
    """
    return any(contains_phrase(message_lower, keyword) for keyword in keyword_list)


def generate_explanation(message):
    message_lower = message.lower()

    warning_signs = []

    urgency_words = [
        "urgent", "immediately", "now", "today", "limited time",
        "expire", "expired", "blocked", "suspended", "avoid suspension",
        "reactivate", "re-activate", "final reminder", "last chance",
        "account locked", "disabled", "permanently disabled"
    ]

    money_words = [
        "fee", "payment", "registration", "processing", "service fee",
        "advance payment", "cash", "loan", "prize", "reward", "tax",
        "release fee", "claim fee", "admin fee", "clearance fee",
        "high return", "guaranteed", "no risk", "daily salary",
        "daily payment", "per day", "rs.", "rs", "lkr"
    ]

    sensitive_words = [
        "otp", "password", "pin", "nic", "card details", "bank details",
        "account number", "login", "credentials", "verification code",
        "debit card", "credit card", "cvv", "passport", "username"
    ]

    link_words = [
        "click here", "click this", "click the", "tap here", "open this link",
        "verify your", "login here", "claim now", "refund now",
        "reactivate", "re-activate", "release now",
        "update details", "update your details", "update your information",
        "[url]"
    ]

    job_scam_words = [
        "we're hiring", "we are hiring", "hiring", "simple job",
        "simple work", "simple work offer", "job for you", "work offer",
        "work from home", "work at home", "do it online", "online job",
        "part time", "full time", "daily salary", "daily payment",
        "per day", "flexible time", "free time job", "1 hour", "2 hour",
        "3 hour", "1-3h", "1hour", "2hour", "no experience",
        "no need experience", "non-experience", "anyone can do",
        "can do at home", "can do with your mobile", "fully support",
        "join now", "apply now", "reply yes", "reply ok", "yes or ok",
        "yes/ok", "for more details", "for more information",
        "data entry", "social media task", "earn daily",

        # Sinhala / Singlish
        "රැකියා", "රැකියාව", "ඇබෑර්තු", "සේවකයින්",
        "අවශ්‍යයි", "දෛනික වැටුප", "ගෙදර සිට", "නිවසේ සිට",
        "අයදුම් කරන්න", "පිළිතුරු දෙන්න", "ඔයාගේ වයස",
        "dawasata", "gedara idan", "wayasa", "weda", "wada",
        "experience one na", "mobile eken",

        # Tamil / Tamil-English
        "வேலை", "சம்பளம்", "part time job", "online velai",
        "daily payment", "work from home"
    ]

    parcel_scam_words = [
        "parcel", "delivery", "courier", "postal", "package", "order",
        "cannot be delivered", "incorrect address", "invalid address",
        "update your information", "update your details",
        "confirm your delivery details", "delivery attempts",
        "item will be returned", "unable to ship", "ship your order",
        "customs", "release parcel", "delivery fee", "reschedule delivery",
        "clearance fee", "package held", "held at customs",

        # Sinhala / Singlish
        "පාර්සල්", "පාර්සලය", "ලිපිනය", "වැරදියි",
        "customs eke", "parcel eka", "address eka", "deliver karanna"
    ]

    banking_scam_words = [
        "bank", "bank account", "online banking", "mobile banking",
        "account blocked", "account suspended", "account locked",
        "debit card", "credit card", "transaction detected",
        "suspicious transaction", "verify account", "bank login",
        "boc", "people's bank", "sampath", "commercial bank",
        "hnb", "ndb", "nsb", "seylan",

        # Sinhala / Singlish
        "බැංකු", "ගිණුම", "bank account eka", "account eka",
        "otp eka", "login details"
    ]

    otp_scam_words = [
        "send otp", "share otp", "reply with otp", "otp required",
        "verification code", "send the code", "forward your otp",
        "otp එක", "otp eka", "code eka", "pin eka",
        "otp அனுப்பவும்", "otp ah reply"
    ]

    loan_scam_words = [
        "instant loan", "easy loan", "no-repayment loan", "loan approval",
        "service fee", "registration charge", "pay first",
        "before disbursement", "mobile wallet", "cash in advance",
        "processing charge", "loan processing"
    ]

    investment_scam_words = [
        "crypto", "investment", "telegram group", "guaranteed return",
        "high return", "no risk", "fixed return", "daily profit",
        "forex", "trading", "ai trading", "private investment group",
        "double returns", "multiply your money"
    ]

    shopping_scam_words = [
        "fake facebook page", "marketplace listing", "unrealistic price",
        "advance payment", "full payment", "personal bank transfer",
        "cash only", "cash-only", "below market price",
        "seller disappeared", "lost suitcase", "only $1", "only rs",
        "go to the website", "click the button"
    ]

    impersonation_words = [
        "fake profile", "fake account", "official page", "verified tick",
        "new account", "few followers", "unusual handle",
        "customer care", "bank officer", "admin support",
        "police department", "sri lanka police", "traffic fine",
        "fine overdue", "payment reminder", "deleted account",
        "unknown", "impersonate", "representative"
    ]

    romance_scam_words = [
        "gift parcel", "customs", "emergency", "refuses video call",
        "new online connection", "send money", "i really love you",
        "love you", "help me", "relationship"
    ]

    lottery_scam_words = [
        "won", "winner", "lottery", "prize", "sweepstake",
        "large sum", "tax fee", "processing fee", "release fee",
        "claim prize", "cash prize", "lucky winner", "reward",
        "voucher", "you won", "you have won"
    ]

    gaming_scam_words = [
        "gaming top-up", "free in-game items", "free diamonds",
        "free coins", "game account", "parental account",
        "credentials", "top up", "free skin"
    ]

    cold_contact_words = [
        "hello..", "hello !!", "he!!o", "h.ello", "h.e.l.l.o",
        "are you there", "are-you-there", "can i talk", "may i talk",
        "excuse me", "nice to meet you", "unknown account greeting",
    ]

    if contains_any(message_lower, urgency_words):
        warning_signs.append("Uses urgent or pressure-based language")

    if contains_any(message_lower, money_words):
        warning_signs.append("Mentions money, fees, prizes, payments, or unrealistic earnings")

    if contains_any(message_lower, sensitive_words):
        warning_signs.append("Requests or mentions sensitive personal or banking information")

    if contains_any(message_lower, link_words):
        warning_signs.append("Encourages clicking a link, verifying details, or updating information")

    if contains_any(message_lower, job_scam_words):
        warning_signs.append("Contains fake job or work-from-home scam indicators")

    if contains_any(message_lower, parcel_scam_words):
        warning_signs.append("Contains parcel, courier, delivery, or customs scam indicators")

    if contains_any(message_lower, banking_scam_words):
        warning_signs.append("Contains bank impersonation or account-security scam indicators")

    if contains_any(message_lower, otp_scam_words):
        warning_signs.append("Mentions OTP, PIN, or verification-code sharing")

    if contains_any(message_lower, loan_scam_words):
        warning_signs.append("Contains instant-loan or advance-fee loan scam indicators")

    if contains_any(message_lower, investment_scam_words):
        warning_signs.append("Contains investment, crypto, or guaranteed-return scam indicators")

    if contains_any(message_lower, shopping_scam_words):
        warning_signs.append("Contains online shopping or fake marketplace scam indicators")

    if contains_any(message_lower, impersonation_words):
        warning_signs.append("Shows possible impersonation of a person, institution, bank, or authority")

    if contains_any(message_lower, romance_scam_words):
        warning_signs.append("Contains romance scam or emotional manipulation indicators")

    if contains_any(message_lower, lottery_scam_words):
        warning_signs.append("Contains lottery, prize, reward, or winner scam indicators")

    if contains_any(message_lower, gaming_scam_words):
        warning_signs.append("Contains gaming top-up or free in-game reward scam indicators")

    if contains_any(message_lower, cold_contact_words):
        warning_signs.append("Uses suspicious cold-contact greeting patterns")

    if not warning_signs:
        warning_signs.append("No major scam indicators were detected from the rule-based explanation layer")

    return warning_signs


def generate_safety_advice(prediction, risk_level):
    prediction = prediction.lower()

    if prediction == "scam" or risk_level == "High Risk":
        return [
            "Do not click any links in the message.",
            "Do not share OTP, PIN, NIC, passwords, card details, or bank account information.",
            "Verify the message only through the official website, app, hotline, or verified social media page.",
            "Block and report the sender if the message came from an unknown or suspicious account."
        ]

    if prediction == "suspicious" or risk_level == "Medium Risk":
        return [
            "Be careful before replying or continuing the conversation.",
            "Do not send money, personal details, or screenshots of banking apps.",
            "Check whether the sender is verified and whether the offer is realistic.",
            "Ask a trusted person or official organization before taking action."
        ]

    return [
        "This message appears low risk, but still verify unknown senders.",
        "Never share OTPs, passwords, PINs, or banking details through chat, SMS, or email."
    ]