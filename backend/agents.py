from langgraph.types import interrupt

def ingestion_agent(state: dict) -> dict:
    file = state["current_slip"]
    raw_text = file["content"]
    fields = {
        "insured": None, "premium": None, "territory": None,
        "coverage": None, "broker": None, "inception": None,
        "expiry": None, "source": file["source"], "filename": file["filename"]
    }

    for line in raw_text.splitlines():
        line = line.strip()
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "insured": fields["insured"] = value
        elif key == "premium": fields["premium"] = value
        elif key in ("territory", "territory/location"): fields["territory"] = value
        elif key in ("coverage", "type"): fields["coverage"] = value
        elif key == "broker": fields["broker"] = value
        elif key == "inception": fields["inception"] = value
        elif key in ("expiry", "period"):
            if "to" in value.lower():
                fields["expiry"] = value.split("to")[-1].strip()
                fields["inception"] = value.split("to")[0].strip()
            else:
                fields["expiry"] = value

    FIELD_KEYWORDS = {
        "insured": ["insured", "client", "policyholder"],
        "premium": ["premium", "price", "cost"],
        "territory": ["territory", "location", "region", "country"],
        "coverage": ["coverage", "cover", "covering", "insuring", "type"],
        "broker": ["broker", "brokerage", "agent"],
        "inception": ["inception", "commencing", "start date"],
        "expiry": ["expiry", "expiring", "expires"],
    }

    def extract_by_split(text, keywords):
        words = text.lower().split()
        for keyword in keywords:
            if keyword in words:
                idx = words.index(keyword)
                value_words = words[idx + 1: idx + 5]
                stop = ["and", "with", "for", "the", "is", "are", "in", "on", "to", "days", "of"]
                clean = []
                for w in value_words:
                    if w in stop:
                        break
                    clean.append(w)
                if clean:
                    return " ".join(clean)
        return None

    for field, keywords in FIELD_KEYWORDS.items():
        if fields[field] is None:
            fields[field] = extract_by_split(raw_text, keywords)

    state["extracted"] = [fields]
    return state


def classification_agent(state: dict) -> dict:
    slip = state["extracted"][0]
    coverage = (slip["coverage"] or "").lower()
    territory = (slip["territory"] or "").lower()

    if "marine cargo" in coverage: slip["lob"] = "Marine"
    elif "aviation" in coverage: slip["lob"] = "Aviation"
    elif "property" in coverage: slip["lob"] = "Property"
    else: slip["lob"] = None

    if "uk" in territory or "united kingdom" in territory or "ireland" in territory:
        slip["region"] = "UK"
    elif "australia" in territory: slip["region"] = "Australia"
    elif "usa" in territory or "united states" in territory: slip["region"] = "USA"
    else: slip["region"] = None

    state["classified"] = [slip]
    return state


def confidence_router(state: dict) -> dict:
    slip = state["classified"][0]
    lob_found = slip["lob"] is not None
    region_found = slip["region"] is not None

    if lob_found and region_found: slip["confidence"] = 0.9
    elif lob_found or region_found: slip["confidence"] = 0.65
    else: slip["confidence"] = 0.25

    if slip["confidence"] >= 0.85:
        slip["status"] = "auto_approved"
    elif slip["confidence"] >= 0.6:
        slip["status"] = "needs_human_review"
        decision = interrupt({
            "slip": slip,
            "message": "Low confidence classification. Please review."
        })
        slip["human_decision"] = decision
    else:
        slip["status"] = "rejected"

    state["routed"] = [slip]
    state["route"] = slip["status"]  # ← now always correct, single slip
    return state


def human_review_agent(state: dict) -> dict:
    slip = state["routed"][0]
    print(f"[HUMAN REVIEW] {slip['filename']}")
    return state


def reject_agent(state: dict) -> dict:
    slip = state["routed"][0]
    print(f"[REJECTED] {slip['filename']}")
    return state