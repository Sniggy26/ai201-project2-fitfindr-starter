"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.
"""

import re
from tools import search_listings, suggest_outfit, create_fit_card


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


# ── query parser ──────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query
    using regex. Returns a dict with keys: description, size, max_price.
    """
    # Extract price (e.g. "under $30", "under 30", "$25")
    price_match = re.search(r'under\s*\$?(\d+(?:\.\d+)?)', query, re.IGNORECASE)
    max_price = float(price_match.group(1)) if price_match else None

    # Extract size (e.g. "size M", "size XL", "size W30")
    size_match = re.search(r'\bsize\s+([A-Za-z0-9/]+)\b', query, re.IGNORECASE)
    size = size_match.group(1) if size_match else None

    # Remove size and price fragments to get clean description
    description = query
    if price_match:
        description = description.replace(price_match.group(0), "")
    if size_match:
        description = description.replace(size_match.group(0), "")
    description = re.sub(r'\$\d+(?:\.\d+)?', '', description)
    description = re.sub(r'\s+', ' ', description).strip(" ,.")

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop and returns
    the completed session dict.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Step 3: Search listings
    results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
    )
    session["search_results"] = results

    # If no results, set error and return early
    if not results:
        session["error"] = (
            "No listings found for your search. "
            "Try a broader description, a different size, or a higher price."
        )
        return session

    # Step 4: Select top result
    session["selected_item"] = results[0]

    # Step 5: Suggest outfit
    outfit = suggest_outfit(session["selected_item"], wardrobe)
    session["outfit_suggestion"] = outfit

    # Step 6: Create fit card
    fit_card = create_fit_card(session["outfit_suggestion"], session["selected_item"])
    session["fit_card"] = fit_card

    # Step 7: Return completed session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")