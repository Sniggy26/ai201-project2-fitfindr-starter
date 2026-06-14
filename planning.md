# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the mock listings dataset and returns items that match the user's description, size, and max price. Returns an empty list if no listings match the filters.

**Input parameters:**
- `description` (str): A natural language description of the item the user is looking for (e.g. "vintage graphic tee")
- `size` (str or None): The size to filter by (e.g. "M", "W30", "S/M") — if None, size is not filtered
- `max_price` (float or None): The maximum price the user is willing to pay — if None, price is not filtered

**What it returns:**
A list of listing dicts, each containing: id, title, description, category, style_tags, size, condition, price, colors, brand, platform. Returns an empty list [] if no matches are found. Never raises an exception.

**What happens if it fails or returns nothing:**
If the list is empty, the agent sets session["error"] = "No listings found for your search. Try a broader description, a different size, or a higher price." The agent stops and does not call suggest_outfit.

---

### Tool 2: suggest_outfit

**What it does:**
Given a specific thrifted item and the user's current wardrobe, uses an LLM to suggest one or more complete outfit combinations. Handles an empty wardrobe by offering general styling advice instead.

**Input parameters:**
- `new_item` (dict): A single listing dict returned by search_listings (contains title, category, style_tags, colors, condition, price, platform)
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of wardrobe item dicts (each with name, category, colors, style_tags, notes)

**What it returns:**
A non-empty string containing one or more outfit suggestions. If the wardrobe is empty, returns general styling advice for the new item based on its style tags and colors. Never returns an empty string or raises an exception.

**What happens if it fails or returns nothing:**
If wardrobe['items'] is empty, the tool generates general styling advice without referencing wardrobe pieces. If the LLM call fails, returns: "Unable to generate outfit suggestion. Please try again."

---

### Tool 3: create_fit_card

**What it does:**
Generates a short, shareable Instagram-style caption describing the complete outfit. Produces varied output each time by using a higher LLM temperature.

**Input parameters:**
- `outfit` (str): The outfit suggestion string returned by suggest_outfit
- `new_item` (dict): The listing dict for the thrifted item (contains title, price, platform)

**What it returns:**
A single string of 1-3 sentences written in casual first-person social media style (e.g. "thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs"). Never returns an empty string or raises an exception.

**What happens if it fails or returns nothing:**
If outfit is an empty string or None, returns the error string: "Cannot create a fit card without an outfit suggestion." If the LLM call fails, returns: "Unable to generate fit card. Please try again."

---

### Additional Tools (if any)

None for required features.

---

## Planning Loop

**How does your agent decide which tool to call next?**

The agent runs a linear loop with conditional branching based on each tool's output:

1. Call search_listings(description, size, max_price)
2. Check if results is empty:
   - If yes: set session["error"] = "No listings found..." and return session early. Do NOT call suggest_outfit.
   - If no: set session["selected_item"] = results[0] and continue.
3. Call suggest_outfit(session["selected_item"], wardrobe)
4. Set session["outfit_suggestion"] = returned string and continue.
5. Call create_fit_card(session["outfit_suggestion"], session["selected_item"])
6. Set session["fit_card"] = returned string.
7. Return the completed session.

The agent never calls all three tools unconditionally — it always checks the result of search_listings before proceeding.

---

## State Management

**How does information from one tool get passed to the next?**

All state is stored in a single session dict initialized at the start of run_agent() and updated after each tool call:

- session["selected_item"]: set after search_listings succeeds — the top result dict
- session["outfit_suggestion"]: set after suggest_outfit returns — the outfit string
- session["fit_card"]: set after create_fit_card returns — the caption string
- session["error"]: set if any tool fails or returns nothing — a human-readable error string

Each tool receives its inputs directly from the session dict. No tool re-prompts the user or re-loads data independently.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Sets session["error"] = "No listings found for your search. Try a broader description, a different size, or a higher price." Returns session early without calling suggest_outfit. |
| suggest_outfit | Wardrobe is empty | Tool detects empty wardrobe['items'] and generates general styling advice based on the new item's style_tags and colors instead of referencing wardrobe pieces. |
| create_fit_card | Outfit input is missing or incomplete | Returns the string "Cannot create a fit card without an outfit suggestion." without calling the LLM. |

---

## Architecture

User query (description, size, max_price, wardrobe)

│

▼

Planning Loop

│

├─► search_listings(description, size, max_price)

│       │

│       ├── results == [] ──► session["error"] = "No listings found..." ──► RETURN (early exit)

│       │

│       └── results != [] ──► session["selected_item"] = results[0]

│                                       │

├─► suggest_outfit(selected_item, wardrobe)

│       │

│       ├── wardrobe empty ──► general styling advice (no crash)

│       │

│       └── session["outfit_suggestion"] = suggestion string

│                                       │

└─► create_fit_card(outfit_suggestion, selected_item)

│

├── outfit empty ──► return error string (no crash)

│

└── session["fit_card"] = caption string

│

▼

Return session

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**

For search_listings: I'll give Claude the Tool 1 spec from this file (inputs, return value, failure mode) and ask it to implement search_listings() using load_listings() from utils/data_loader.py. I'll verify the generated code filters by all three parameters, handles None values for size and max_price, and returns [] on no match. Then I'll test it with 3 queries before using it.

For suggest_outfit: I'll give Claude the Tool 2 spec and ask it to implement suggest_outfit() using Groq's llama-3.3-70b-versatile. I'll verify it handles empty wardrobe['items'] without crashing and always returns a non-empty string.

For create_fit_card: I'll give Claude the Tool 3 spec and ask it to implement create_fit_card() with a higher temperature setting. I'll run it 3 times on the same input and verify the outputs differ. I'll also test it with an empty outfit string to confirm the error message is returned.

**Milestone 4 — Planning loop and state management:**

I'll give Claude the Planning Loop and State Management sections from this file plus the Architecture diagram and ask it to implement run_agent() in agent.py. I'll verify the generated code branches on search_listings results, stores values in the session dict, and does not call all three tools unconditionally.

---

## A Complete Interaction (Step by Step)

FitFindr is a multi-tool AI agent that helps users find secondhand clothing and build outfits around new thrifted pieces. When a user describes what they're looking for, the agent searches mock listings filtered by description, size, and price, then uses the best match to suggest outfit combinations based on the user's existing wardrobe. If any step fails — no listings found, empty wardrobe, or incomplete outfit data — the agent responds with a specific, helpful message rather than crashing or continuing with bad input.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
Call search_listings("vintage graphic tee", size=None, max_price=30.0). The function loads listings.json, filters by price <= 30 and checks if "vintage", "graphic", or "tee" appear in the title, description, or style_tags. Returns a list of matching items — e.g. [{"id": "lst_006", "title": "Graphic Tee — 2003 Tour Bootleg Style", "price": 24.0, "platform": "depop", ...}]. Sets session["selected_item"] = results[0].

**Step 2:**
Call suggest_outfit(session["selected_item"], get_example_wardrobe()). The LLM receives the new item's details and the user's 10 wardrobe items and returns a suggestion like: "Pair this boxy bootleg tee with your baggy dark wash jeans and chunky white sneakers for an easy 90s streetwear look. Throw your black denim jacket on top if it gets cold." Sets session["outfit_suggestion"] = that string.

**Step 3:**
Call create_fit_card(session["outfit_suggestion"], session["selected_item"]). The LLM generates a casual caption like: "thrifted this bootleg tee off depop for $24 and it goes with literally everything in my closet — baggy jeans and chunky sneakers and we're done 🖤". Sets session["fit_card"] = that string.

**Final output to user:**
The Gradio interface displays three panels: the top search result (title, price, platform, condition), the outfit suggestion, and the fit card caption.