import unicodedata
import re

CITY_MAP = {
    # Toronto variants
    "toronto": "Toronto",
    "toronto ontario": "Toronto",
    "west toronto": "Toronto",
    "downtown toronto": "Toronto",
    "north toronto": "Toronto",
    "toronto division": "Toronto",
    "tonronto": "Toronto",
    "tornto": "Toronto",
    "totronto": "Toronto",
    # Montreal variants
    "montreal": "Montreal",
    "montral": "Montreal",
    "monteal": "Montreal",
    "montreal nord": "Montreal",
    "montreal ouest": "Montreal",
    "montreal quest": "Montreal",
    "montreal west": "Montreal",
    "communaute urbaine de montreal": "Montreal",
    "montreal quebec": "Montreal",
    "vieux montreal": "Montreal",
    "old port of montreal": "Montreal",
    "outremont": "Montreal",
    "mont royal": "Montreal",
}


def normalize_city(city: str) -> str:
    """
    Normalize a city string:
    - Strip whitespace
    - Remove accents (é -> e, é -> e, etc.)
    - Lowercase
    - Remove special characters (hyphens, commas, dots)
    - Collapse multiple spaces
    """
    if not isinstance(city, str):
        return ""
    # Remove accents
    city = unicodedata.normalize("NFD", city)
    city = "".join(c for c in city if unicodedata.category(c) != "Mn")
    # Lowercase
    city = city.lower()
    # Remove special characters, keep only letters and spaces
    city = re.sub(r"[^a-z\s]", " ", city)
    # Collapse multiple spaces and strip
    city = re.sub(r"\s+", " ", city).strip()
    return city


def clean_city(city: str) -> str | None:
    """
    Returns 'Toronto', 'Montreal', or None if the city
    doesn't match either target.
    """
    normalized = normalize_city(city)
    return CITY_MAP.get(normalized, city)
