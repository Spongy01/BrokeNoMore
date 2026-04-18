import csv
import io
from datetime import date
from decimal import Decimal

from schemas import TransactionCreate

CHASE_SKIP_DESCRIPTIONS = [
    "discover", "zelle payment to", "zelle payment from"
]

CHASE_KEYWORD_MAP = {
    "Food & Dining": [
        "aldi", "wholefds", "whole foods", "walmart grocery",
        "trader joe", "target grocery", "mcdonald", "chipotle",
        "subway", "dunkin", "starbucks", "doordash", "ubereats",
        "grubhub", "instacart",
    ],
    "Transportation": [
        "uber", "lyft", "mta", "suffolk", "masabi", "fastfare",
        "gas", "exxon", "shell", "bp ", "parking", "metro",
    ],
    "Entertainment": [
        "steam", "steamgames", "netflix", "spotify", "hulu",
        "disney", "apple.com/bill", "playstation", "xbox",
        "amazon prime", "youtube",
    ],
    "Shopping": [
        "amazon", "walmart", "target", "bestbuy", "ebay",
        "etsy", "shein", "zara", "claude.ai",
    ],
    "Health & Medical": [
        "pharmacy", "cvs", "walgreens", "rite aid", "doctor",
        "hospital", "dental", "vision",
    ],
    "Education": [
        "tuition", "coursera", "udemy", "chegg",
    ],
    "Bills & Utilities": [
        "verizon", "att", "t-mobile", "spectrum", "con ed",
        "electric", "insurance",
    ],
}

DISCOVER_SKIP_CATEGORIES = {
    "payments and credits",
    "cashback bonus",
    "fees",
}

DISCOVER_CATEGORY_MAP = {
    "restaurants":           "Food & Dining",
    "supermarkets":          "Food & Dining",
    "gas stations":          "Transportation",
    "travel/ entertainment": "Entertainment",
    "merchandise":           "Shopping",
    "services":              "Other",
    "government services":   "Other",
    "healthcare":            "Health & Medical",
    "education":             "Education",
    "automotive":            "Transportation",
    "home improvement":      "Shopping",
}


def _parse_date(date_str: str) -> date:
    from datetime import datetime
    return datetime.strptime(date_str.strip(), "%m/%d/%Y").date()


def _classify_chase(description: str) -> str:
    lower = description.lower()
    for category, keywords in CHASE_KEYWORD_MAP.items():
        if any(kw in lower for kw in keywords):
            return category
    return "Other"


def _parse_chase(
    reader: csv.DictReader, user_id: str, source: str
) -> tuple[list[TransactionCreate], list[str]]:
    transactions: list[TransactionCreate] = []
    skipped: list[str] = []

    for row in reader:
        description = row["Description"].strip()
        lower_desc = description.lower()

        if any(skip in lower_desc for skip in CHASE_SKIP_DESCRIPTIONS):
            skipped.append(description)
            continue

        amount = Decimal(row["Amount"].strip())
        transaction_type = "credit" if amount >= 0 else "debit"

        transactions.append(TransactionCreate(
            user_id=user_id,
            amount=abs(amount),
            transaction_type=transaction_type,
            category=_classify_chase(description),
            description=description,
            date=_parse_date(row["Posting Date"]),
            source=source,
        ))

    return transactions, skipped


def _parse_discover(
    reader: csv.DictReader, user_id: str, source: str
) -> tuple[list[TransactionCreate], list[str]]:
    transactions: list[TransactionCreate] = []
    skipped: list[str] = []

    for row in reader:
        raw_category = row["Category"].strip()
        if raw_category.lower() in DISCOVER_SKIP_CATEGORIES:
            skipped.append(row["Description"].strip())
            continue

        description = row["Description"].strip()
        # Discover: positive = debit, negative = credit (flipped vs Chase)
        amount = Decimal(row["Amount"].strip())
        transaction_type = "debit" if amount >= 0 else "credit"

        category = DISCOVER_CATEGORY_MAP.get(raw_category.lower(), "Other")

        transactions.append(TransactionCreate(
            user_id=user_id,
            amount=abs(amount),
            transaction_type=transaction_type,
            category=category,
            description=description,
            date=_parse_date(row["Trans. Date"]),
            source=source,
        ))

    return transactions, skipped


async def parse_csv(
    content: bytes,
    user_id: str,
    source: str,
) -> tuple[list[TransactionCreate], list[str]]:
    text = content.decode("utf-8-sig")  # utf-8-sig strips BOM if present
    reader = csv.DictReader(io.StringIO(text))

    if source == "Chase Checking":
        return _parse_chase(reader, user_id, source)
    elif source == "Discover Credit":
        return _parse_discover(reader, user_id, source)
    else:
        raise ValueError(f"Unknown source: {source!r}. Expected 'Chase Checking' or 'Discover Credit'.")
