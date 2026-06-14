"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os
from dotenv import load_dotenv
from groq import Groq
from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts sorted by relevance, or [] if none match.
    """
    listings = load_listings()

    # Step 1: Filter by max_price and size
    filtered = []
    for item in listings:
        if max_price is not None and item["price"] > max_price:
            continue
        if size is not None and size.lower() not in item["size"].lower():
            continue
        filtered.append(item)

    # Step 2: Score by keyword overlap with description
    keywords = description.lower().split()
    scored = []
    for item in filtered:
        searchable = " ".join([
            item["title"],
            item["description"],
            item["category"],
            " ".join(item["style_tags"]),
            " ".join(item["colors"]),
            item["brand"] or "",
        ]).lower()

        score = sum(1 for kw in keywords if kw in searchable)
        if score > 0:
            scored.append((score, item))

    # Step 3: Sort by score descending and return listing dicts
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1-2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key. May be empty.

    Returns:
        A non-empty string with outfit suggestions or general styling advice.
    """
    try:
        client = _get_groq_client()
        wardrobe_items = wardrobe.get("items", [])

        if not wardrobe_items:
            prompt = f"""You are a thrift fashion stylist. A user is considering buying this secondhand item:

Item: {new_item['title']}
Category: {new_item['category']}
Style tags: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}
Condition: {new_item['condition']}

They haven't shared their wardrobe yet. Give them 1-2 general outfit ideas — what types of pieces pair well with this item, what vibe it suits, and how to style it. Be specific about silhouettes, colors, and occasions."""
        else:
            wardrobe_text = "\n".join([
                f"- {i['name']} ({i['category']}, colors: {', '.join(i['colors'])}, style: {', '.join(i['style_tags'])})"
                for i in wardrobe_items
            ])
            prompt = f"""You are a thrift fashion stylist. A user is considering buying this secondhand item:

Item: {new_item['title']}
Category: {new_item['category']}
Style tags: {', '.join(new_item['style_tags'])}
Colors: {', '.join(new_item['colors'])}
Condition: {new_item['condition']}

Their current wardrobe includes:
{wardrobe_text}

Suggest 1-2 specific outfit combinations using the new item and named pieces from their wardrobe. Be specific about which pieces to combine and why they work together."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        result = response.choices[0].message.content.strip()
        return result if result else "Unable to generate outfit suggestion. Please try again."

    except Exception:
        return "Unable to generate outfit suggestion. Please try again."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2-4 sentence casual Instagram-style caption string.
    """
    if not outfit or not outfit.strip():
        return "Cannot create a fit card without an outfit suggestion."

    try:
        client = _get_groq_client()

        prompt = f"""You are writing an Instagram caption for a thrift outfit post. Write a 2-3 sentence caption that:
- Sounds casual and authentic, like a real person posting their OOTD
- Mentions the item "{new_item['title']}" naturally
- Mentions the price ${new_item['price']} and platform {new_item['platform']} once
- Captures this outfit vibe: {outfit[:300]}
- Uses lowercase, feels genuine, not like an ad

Write only the caption. No hashtags. No explanation."""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=1.0,
        )
        result = response.choices[0].message.content.strip()
        return result if result else "Unable to generate fit card. Please try again."

    except Exception:
        return "Unable to generate fit card. Please try again."