# ── INGESTION AGENT ──────────────────────────────────────────
def ingestion_agent(state: dict) -> dict:
    """Extract 7 fields from raw slip text using line-by-line parsing."""
    results = []

    for file in state["new_files"]:
        raw_text = file["content"]
        fields = {
            "insured": None,
            "premium": None,
            "territory": None,
            "coverage": None,
            "broker": None,
            "inception": None,
            "expiry": None,
            "source": file["source"],
            "filename": file["filename"]
        }

        for line in raw_text.splitlines():
            line = line.strip()
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()

            if key == "insured":
                fields["insured"] = value
            elif key == "premium":
                fields["premium"] = value
            elif key == "territory":
                fields["territory"] = value
            elif key == "coverage":
                fields["coverage"] = value
            elif key == "broker":
                fields["broker"] = value
            elif key == "inception":
                fields["inception"] = value
            elif key == "expiry":
                fields["expiry"] = value

        results.append(fields)

    state["extracted"] = results
    return state


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