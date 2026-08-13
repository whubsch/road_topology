"""
Highway hierarchy definitions and classification utilities.

OSM highway types ordered from most to least important (lower rank = higher importance).
We only analyse down to `tertiary`; unclassified/residential are the expected
lower-class neighbours and are not flagged themselves.
"""

from typing import Optional

# Rank map: lower number = more important road
# fmt: off
HIGHWAY_RANK: dict[str, int] = {
    "motorway":       1,
    "motorway_link":  1,
    "trunk":          2,
    "trunk_link":     2,
    "primary":        3,
    "primary_link":   3,
    "secondary":      4,
    "secondary_link": 4,
    "tertiary":       5,
    "tertiary_link":  5,
    # Lower classes are valid downgrade neighbours but are NOT analysed themselves
    "unclassified":   6,
    "residential":    6,
    "living_street":  6,
    "service":        7,
    "track":          8,
    "path":           9,
    "cycleway":       9,
    "footway":        9,
    "pedestrian":     9,
    "steps":          9,
}
# fmt: on

# Maximum rank that will be *checked* for topology errors.
# Ways with rank > ANALYSED_MAX_RANK are only used as connecting neighbours.
ANALYSED_MAX_RANK: int = 5  # tertiary / tertiary_link

# Display label for error messages
RANK_LABEL: dict[int, str] = {
    1: "motorway/motorway_link",
    2: "trunk/trunk_link",
    3: "primary/primary_link",
    4: "secondary/secondary_link",
    5: "tertiary/tertiary_link",
    6: "unclassified/residential",
    7: "service",
    8: "track",
    9: "path/footway/cycleway",
}


# Canonical highway tag value for a given rank (used when guessing a fix).
# Rank 6 is ambiguous between unclassified/residential; we default to
# "unclassified" as the more conservative / lower-traffic guess.
RANK_TO_HIGHWAY: dict[int, str] = {
    1: "motorway",
    2: "trunk",
    3: "primary",
    4: "secondary",
    5: "tertiary",
    6: "unclassified",
    7: "service",
    8: "track",
    9: "path",
}

# Ranks (1-5) that have a "_link" variant in OSM.
LINK_ELIGIBLE_RANKS = {1, 2, 3, 4, 5}


def rank_to_highway(rank: int, is_link: bool = False) -> Optional[str]:
    """Return the canonical highway tag value for a rank.

    If `is_link` is True and the rank supports a _link variant, the
    "_link" suffixed tag is returned instead.
    """
    base = RANK_TO_HIGHWAY.get(rank)
    if base is None:
        return None
    if is_link and rank in LINK_ELIGIBLE_RANKS:
        return f"{base}_link"
    return base


def get_rank(highway_value: str) -> Optional[int]:
    """Return the numeric rank for a highway tag value, or None if unknown."""
    return HIGHWAY_RANK.get(highway_value)


def is_analysed(highway_value: str) -> bool:
    """Return True if this highway type should be checked for topology errors."""
    rank = get_rank(highway_value)
    return rank is not None and rank <= ANALYSED_MAX_RANK


def is_valid_neighbour(highway_value: str) -> bool:
    """Return True if this highway type counts as a valid connecting road."""
    return highway_value in HIGHWAY_RANK


def qualifies_as_upgrade(neighbour_rank: int, way_rank: int) -> bool:
    """
    Return True if a neighbour road is of equal or higher class than the
    way under analysis (i.e. it satisfies the topology requirement).

    Equal rank always qualifies. A lower rank number = higher importance,
    so neighbour_rank <= way_rank means the neighbour is at least as important.
    """
    return neighbour_rank <= way_rank
