# ── INGESTION AGENT ──────────────────────────────────────────
def ingestion_agent(state: dict) -> dict:
    """Extract 7 fields - tries Key:Value first, falls back to split() for sentences."""
    results = []

    FIELD_KEYWORDS = {
        "insured": ["insured", "client", "policyholder"],
        "premium": ["premium", "price", "cost"],
        "territory": ["territory", "location", "region", "country"],
        "coverage": ["coverage", "cover", "covering", "insuring"],
        "broker": ["broker", "brokerage", "agent"],
        "inception": ["inception", "start", "commencing", "from"],
        "expiry": ["expiry", "expiring", "expires", "until", "to"],
    }

    def extract_by_split(text: str, keywords: list) -> str:
        """Scan sentence words for a keyword and grab the following words."""
        words = text.lower().split()
        for keyword in keywords:
            if keyword in words:
                idx = words.index(keyword)
                # grab up to 4 words after the keyword
                value_words = words[idx + 1: idx + 5]
                # stop at common stop words
                stop = ["and", "with", "for", "the", "is", "are", "in", "on"]
                clean = []
                for w in value_words:
                    if w in stop:
                        break
                    clean.append(w)
                if clean:
                    return " ".join(clean)
        return None

    for file in state["new_files"]:
        raw_text = file["content"]
        fields = {
            "insured": None,
            "premium": None,
            "territory": None,
            "coverage": None,
            "broker": None,
            "inception": None,
            

# ── CLASSIFICATION AGENT ─────────────────────────────────────
def classification_agent(state: dict) -> dict:
    """Apply keyword rules to assign LOB and region."""

    for slip in state["extracted"]:
        coverage = (slip["coverage"] or "").lower()
        territory = (slip["territory"] or "").lower()

        # Line of Business rules
        if "marine cargo" in coverage:
            slip["lob"] = "Marine"
        elif "aviation" in coverage:
            slip["lob"] = "Aviation"
        elif "property" in coverage:
            slip["lob"] = "Property"
        else:
            slip["lob"] = None

        # Region rules
        if "uk" in territory or "united kingdom" in territory or "ireland" in territory:
            slip["region"] = "UK"
        elif "australia" in territory:
            slip["region"] = "Australia"
        elif "usa" in territory or "united states" in territory:
            slip["region"] = "USA"
        else:
            slip["region"] = None

    state["classified"] = state["extracted"]
    return state


# ── CONFIDENCE ROUTER ────────────────────────────────────────
def confidence_router(state: dict) -> dict:
    """Score each slip and route based on confidence threshold."""

    for slip in state["classified"]:
        lob_found = slip["lob"] is not None
        region_found = slip["region"] is not None

        if lob_found and region_found:
            slip["confidence"] = 0.9
        elif lob_found or region_found:
            slip["confidence"] = 0.65
        else:
            slip["confidence"] = 0.25

        # Routing decision
        if slip["confidence"] >= 0.85:
            slip["status"] = "auto_approved"
        elif slip["confidence"] >= 0.6:
            slip["status"] = "needs_human_review"
        else:
            slip["status"] = "rejected"

    state["routed"] = state["classified"]
    return state