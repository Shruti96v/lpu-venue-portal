"""
menu.py - the restaurant's menu, starting stock, and name matching.

Customers (and LLMs) write dish names in many ways: "paneer tikka", "Paneer Tikka",
"dal makhni". resolve_item() turns any of those into the one official menu name.
"""
import difflib
import re

# name -> price (Rs.), category, minutes to cook, other names customers use
MENU = {
    "Paneer Tikka":         {"price": 220, "category": "starter", "prep_min": 15, "aliases": ["tikka", "paneer tika"]},
    "Hara Bhara Kebab":     {"price": 180, "category": "starter", "prep_min": 12, "aliases": ["hara bhara", "veg kebab"]},
    "Dal Makhani":          {"price": 260, "category": "dal",     "prep_min": 20, "aliases": ["dal makhni", "daal makhani", "makhani dal", "black dal"]},
    "Dal Tadka":            {"price": 200, "category": "dal",     "prep_min": 15, "aliases": ["tadka", "daal tadka", "yellow dal"]},
    "Butter Chicken":       {"price": 320, "category": "main",    "prep_min": 20, "aliases": ["murgh makhani", "chicken makhani"]},
    "Paneer Butter Masala": {"price": 280, "category": "main",    "prep_min": 18, "aliases": ["pbm", "paneer makhani"]},
    "Veg Biryani":          {"price": 240, "category": "main",    "prep_min": 22, "aliases": ["biryani", "veg biriyani"]},
    "Butter Naan":          {"price": 50,  "category": "bread",   "prep_min": 6,  "aliases": []},
    "Garlic Naan":          {"price": 60,  "category": "bread",   "prep_min": 6,  "aliases": []},
    "Tandoori Roti":        {"price": 30,  "category": "bread",   "prep_min": 5,  "aliases": ["roti"]},
    "Cold Drink":           {"price": 60,  "category": "drink",   "prep_min": 1,  "aliases": ["coke", "cola", "soft drink", "soda", "pepsi"]},
    "Masala Chai":          {"price": 40,  "category": "drink",   "prep_min": 5,  "aliases": ["chai", "tea"]},
    "Sweet Lassi":          {"price": 80,  "category": "drink",   "prep_min": 3,  "aliases": ["lassi"]},
    "Gulab Jamun":          {"price": 90,  "category": "dessert", "prep_min": 3,  "aliases": ["jamun"]},
}

# How many portions the kitchen has at the start of a session.
# Dal Makhani is 0 on purpose so we can demonstrate "out of stock + alternative".
INITIAL_STOCK = {
    "Paneer Tikka": 12, "Hara Bhara Kebab": 8, "Dal Makhani": 0, "Dal Tadka": 15,
    "Butter Chicken": 10, "Paneer Butter Masala": 10, "Veg Biryani": 8,
    "Butter Naan": 30, "Garlic Naan": 25, "Tandoori Roti": 40,
    "Cold Drink": 40, "Masala Chai": 30, "Sweet Lassi": 15, "Gulab Jamun": 6,
}


def money(amount):
    return f"Rs.{amount:,.2f}"


def _normalise(text):
    """lower-case, keep letters/digits only, single spaces."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _lookup_table():
    """normalised name or alias -> official menu name"""
    table = {}
    for name, data in MENU.items():
        table[_normalise(name)] = name
        for alias in data["aliases"]:
            table[_normalise(alias)] = name
    return table


def alias_pairs():
    """(normalised text, official name) pairs, longest first. Used by the mock parser."""
    table = _lookup_table()
    return sorted(table.items(), key=lambda kv: len(kv[0]), reverse=True)


def resolve_item(text):
    """Return the official menu name for `text`, or None if we cannot tell."""
    query = _normalise(text)
    if not query:
        return None
    table = _lookup_table()
    # 1) exact name or alias
    if query in table:
        return table[query]
    # 2) a full name / multi-word alias hidden inside a longer phrase ("plate of paneer tikka")
    for key in sorted(table, key=len, reverse=True):
        if " " in key and re.search(rf"\b{re.escape(key)}s?\b", query):
            return table[key]
    # 3) small spelling mistakes ("paner tikka")
    close = difflib.get_close_matches(query, list(table), n=1, cutoff=0.8)
    return table[close[0]] if close else None


def suggest_items(text):
    """Menu names that look related to `text` (used in error messages so the LLM can retry)."""
    words = set(_normalise(text).split())
    related = [n for n in MENU if words & set(_normalise(n).split())]
    if related:
        return related
    close = difflib.get_close_matches(_normalise(text), [_normalise(n) for n in MENU], n=3, cutoff=0.5)
    by_norm = {_normalise(n): n for n in MENU}
    return [by_norm[c] for c in close]
