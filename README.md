# FitFindr 🛍️

A multi-tool AI agent that helps users find secondhand clothing and build outfits around new thrifted pieces.

## How to Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Add your GROQ_API_KEY to a .env file
python3 app.py
```

Open http://127.0.0.1:7860 in your browser.

---

## Tool Inventory

### search_listings(description: str, size: str | None, max_price: float | None) → list[dict]
Searches the mock listings dataset for items matching the user's description, size, and price ceiling. Scores each listing by keyword overlap with the description and sorts results by relevance. Returns an empty list if nothing matches — never raises an exception.

### suggest_outfit(new_item: dict, wardrobe: dict) → str
Given a thrifted item and the user's wardrobe, uses Groq's llama-3.3-70b-versatile to suggest 1-2 complete outfit combinations using named wardrobe pieces. If the wardrobe is empty, generates general styling advice based on the item's style tags and colors instead.

### create_fit_card(outfit: str, new_item: dict) → str
Generates a 2-3 sentence casual Instagram-style caption for the outfit. Uses a higher LLM temperature (1.0) to ensure varied output. Guards against an empty outfit string and returns a descriptive error message instead of crashing.

---

## How the Planning Loop Works

The agent runs a linear loop with conditional branching based on each tool's output:

1. Parse the user's query using regex to extract description, size, and max_price.
2. Call search_listings() with the parsed parameters.
3. Check if results is empty — if yes, set session["error"] and return early. Do NOT call suggest_outfit.
4. Set session["selected_item"] = results[0] and call suggest_outfit().
5. Set session["outfit_suggestion"] and call create_fit_card().
6. Set session["fit_card"] and return the completed session.

The agent never calls all three tools unconditionally — it always branches on the search_listings result before proceeding.

---

## State Management

All state is stored in a single session dict initialized at the start of run_agent() and updated after each tool call:

- session["parsed"]: extracted description, size, max_price from the query
- session["search_results"]: full list returned by search_listings
- session["selected_item"]: top result dict, passed into suggest_outfit
- session["outfit_suggestion"]: string returned by suggest_outfit, passed into create_fit_card
- session["fit_card"]: final caption string returned by create_fit_card
- session["error"]: set if any tool fails — signals early termination

No tool re-prompts the user or reloads data independently. Everything flows through the session dict.

---

## Error Handling

### search_listings
Failure mode: no listings match the query. The tool returns [] without raising an exception. The agent detects the empty list, sets session["error"] = "No listings found for your search. Try a broader description, a different size, or a higher price." and returns the session early without calling suggest_outfit.

Example from testing:
search_listings("designer ballgown", size="XXS", max_price=5) → []

run_agent("designer ballgown size XXS under $5", ...) → session["error"] = "No listings found..."

### suggest_outfit
Failure mode: wardrobe is empty. The tool detects wardrobe["items"] == [] and calls the LLM with a prompt for general styling advice instead of outfit combinations. Always returns a non-empty string.

Example from testing:
suggest_outfit(results[0], get_empty_wardrobe()) → "The Y2K Baby Tee pairs well with flowy midi skirts..."

### create_fit_card
Failure mode: outfit string is empty or None. The tool guards against this before calling the LLM and returns "Cannot create a fit card without an outfit suggestion." immediately.

Example from testing:
create_fit_card("", results[0]) → "Cannot create a fit card without an outfit suggestion."

---

## Spec Reflection

One way the spec helped: writing the planning loop in plain conditional logic in planning.md before touching agent.py made the implementation straightforward — the spec became a direct translation into code with no ambiguity about branching.

One way implementation diverged: the spec described query parsing as a simple step but didn't specify how to do it. I implemented regex-based parsing to extract size and price from natural language, which wasn't in the original spec but was necessary for the agent to work end-to-end without requiring structured input from the user.

---

## AI Usage

### Instance 1: Implementing tools.py
I gave Claude the Tool 1, 2, and 3 specs from planning.md (inputs, return values, failure modes) and asked it to implement each function using load_listings() from the data loader and Groq's llama-3.3-70b-versatile. I verified each generated function matched my spec parameters, handled the failure modes I described, and tested each tool in isolation with 3 queries before moving on. I adjusted the temperature for create_fit_card to 1.0 after verifying outputs were too similar at the default setting.

### Instance 2: Implementing agent.py
I gave Claude the Planning Loop, State Management, and Architecture sections from planning.md and asked it to implement run_agent(). I reviewed the generated code to confirm it branched on search_listings results, stored values in the session dict correctly, and did not call all three tools unconditionally. I also added the regex query parser (_parse_query) which was not in the original generated code but was needed to extract structured parameters from natural language queries.