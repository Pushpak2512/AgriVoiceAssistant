# ============================================================
# QUERY PROCESSOR
# AgriVoiceAssistant
# ============================================================

import re


# ============================================================
# CROP KEYWORDS
# ============================================================

CROP_KEYWORDS = {

    "soybean": [
        "soybean",
        "soyabean",
        "soy bean",
        "soy",
        "सोयाबीन",
        "सोयाबीन",
        "सोया"
    ],

    "cotton": [
        "cotton",
        "kapas",
        "कपास",
        "कापूस"
    ],

    "tomato": [
        "tomato",
        "tomatoes",
        "टमाटर",
        "टोमॅटो",
        "टोमॅटो",
        "टमाटा"
    ],

    "onion": [
        "onion",
        "onions",
        "प्याज",
        "प्याज़",
        "कांदा",
        "कांदे"
    ],

    "cabbage": [
        "cabbage",
        "गोभी",
        "कोबी"
    ]
}


# ============================================================
# DETECT CROP
# ============================================================

def detect_crop(query):
    """
    Detect the main crop mentioned in the farmer's query.

    Returns:
        crop name as string, or None
    """

    if not query:
        return None

    text = str(query).lower().strip()

    for crop, keywords in CROP_KEYWORDS.items():

        for keyword in keywords:

            if keyword.lower() in text:
                return crop

    return None


# ============================================================
# DETECT AGRICULTURAL INTENT
# ============================================================

def detect_intent(query):

    if not query:
        return "general"

    text = str(query).lower()

    if any(word in text for word in [
        "rain",
        "rainfall",
        "heavy rainfall",
        "बारिश",
        "वर्षा",
        "पाऊस",
        "अतिवृष्टी"
    ]):
        return "rainfall"

    if any(word in text for word in [
        "sowing",
        "sow",
        "planting",
        "पेरणी",
        "बुवाई",
        "लावणी"
    ]):
        return "sowing"

    if any(word in text for word in [
        "fertilizer",
        "fertiliser",
        "खत",
        "उर्वरक"
    ]):
        return "fertilizer"

    if any(word in text for word in [
        "disease",
        "रोग",
        "रोगराई"
    ]):
        return "disease"

    if any(word in text for word in [
        "pest",
        "insect",
        "कीड",
        "कीटक",
        "किड"
    ]):
        return "pest"

    if any(word in text for word in [
        "weed",
        "weeds",
        "तण",
        "खरपतवार"
    ]):
        return "weed"

    if any(word in text for word in [
        "harvest",
        "harvesting",
        "काढणी",
        "कटाई"
    ]):
        return "harvesting"

    return "general"


# ============================================================
# QUERY EXPANSION
# ============================================================

def expand_query(query):
    """
    Expand a farmer query slightly before FAISS retrieval.

    We deliberately keep the original query intact and append
    agricultural context rather than replacing it.
    """

    if not query:
        return ""

    original = str(query).strip()

    crop = detect_crop(original)
    intent = detect_intent(original)

    additions = []

    # --------------------------------------------------------
    # Crop context
    # --------------------------------------------------------

    if crop:
        additions.append(crop)

    # --------------------------------------------------------
    # Intent context
    # --------------------------------------------------------

    intent_terms = {

        "rainfall": [
            "rainfall",
            "heavy rain",
            "water management",
            "drainage",
            "crop advisory"
        ],

        "sowing": [
            "sowing",
            "planting",
            "seed",
            "crop advisory"
        ],

        "fertilizer": [
            "fertilizer",
            "nutrient management",
            "crop advisory"
        ],

        "disease": [
            "disease",
            "disease management",
            "crop protection"
        ],

        "pest": [
            "pest",
            "insect",
            "pest management",
            "crop protection"
        ],

        "weed": [
            "weed management",
            "weed control",
            "crop advisory"
        ],

        "harvesting": [
            "harvesting",
            "harvest",
            "crop advisory"
        ],

        "general": [
            "agricultural advisory",
            "crop management"
        ]
    }

    additions.extend(
        intent_terms.get(
            intent,
            intent_terms["general"]
        )
    )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    clean_additions = []

    for item in additions:

        if item.lower() not in [
            x.lower()
            for x in clean_additions
        ]:

            clean_additions.append(item)

    # --------------------------------------------------------
    # Final expanded query
    # --------------------------------------------------------

    expanded_query = (
        original
        + " "
        + " ".join(clean_additions)
    )

    return expanded_query.strip()