from ReportType import ReportType

TAGS = {
    "food": {
        2: "food quality",
        3: "taste",
        5: "timing",
        7: "other",
        11: "breakfast",
        13: "lunch",
        17: "snacks",
        19: "dinner"
    },
    "washroom": {
        2: "cleanliness",
        3: "plumbing or maintenance",
        5: "lack of supplies",
        7: "other",
        11: "completely clean",
        13: "dirty floor",
        17: "dirty toilets",
        19: "dirty basins",
        23: "other"
    },
    "water": {
        2: "RO system malfunction",
        3: "poor water quality",
        5: "no water supply",
        7: "water cooler not working",
        11: "other"
    },
    "cleaning": {
        2: "dirty floors",
        3: "trash not emptied",
        5: "spills or stains",
        7: "other"
    },
    "other": {
        2: "safety",
        3: "facility maintenance",
        5: "general complaints or suggestions",
        7: "other"
    }
}


def parseTags(num_tags: int, report_type: ReportType) -> list[str]:
    tags = []
    for tag in TAGS[report_type.name.lower()]:
        if num_tags % tag == 0:
            tags.append(TAGS[report_type.name.lower()][tag])

    return tags
