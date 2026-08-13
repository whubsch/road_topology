"""
Graph builder and topology checker.

Builds a node → ways index from parsed way data, then checks each
analysed way for the topology rule:

    A way of rank R is flagged if BOTH of its terminus nodes connect
    *only* to roads of rank > R (i.e. less important roads).

    If either terminus has at least one road of rank <= R (equal or higher
    importance), the way is topologically sound and is not flagged.

    Ways where one terminus has no connecting road at all (dead-end /
    cul-de-sac / map boundary) are SKIPPED — we only flag ways that
    are connected on both ends but still to lower-class roads only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from .hierarchy import get_rank, is_analysed, qualifies_as_upgrade, rank_to_highway
from .parser import NodeCoord, WayRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class TerminusInfo:
    """Describes the connectivity at one terminus node of a flagged way."""

    node_id: int
    lat: Optional[float]
    lon: Optional[float]
    # highway tags of all roads meeting at this node (excluding the way itself)
    connecting_highways: list[str]
    # minimum rank found among connecting roads (None = no connections)
    min_connecting_rank: Optional[int]

    @property
    def has_connections(self) -> bool:
        return bool(self.connecting_highways)

    @property
    def has_qualifying_connection(self) -> bool:
        """True if at least one connecting road is of equal-or-higher importance."""
        return self.min_connecting_rank is not None


@dataclass
class FlaggedWay:
    way_id: int
    name: Optional[str]
    highway: str
    rank: int
    start: TerminusInfo
    end: TerminusInfo
    version: int
    changeset: int
    user: str
    timestamp: str

    def osm_url(self) -> str:
        """OpenStreetMap object page."""
        return f"https://www.openstreetmap.org/way/{self.way_id}"

    def josm_url(self) -> str:
        """JOSM editor link (requires JOSM to be running)."""
        return (
            f"http://localhost:8111/load_object?new_layer=false&objects=w{self.way_id}"
        )

    def id_url(self) -> str:
        """iD editor link."""
        return f"https://www.openstreetmap.org/edit?editor=id&way={self.way_id}"

    def level0_url(self) -> str:
        """Level0 editor link."""
        return f"https://level0.osmz.ru/?url=w{self.way_id}"

    def suggested_highway(self) -> Optional[str]:
        """
        Guess the correct `highway` tag value for this way based on the
        connectivity of its two termini and whether it carries a name.

        Since this way was flagged, both termini connect only to roads of
        a *lower* classification than the way's current tag. That implies
        the way is very likely over-classified, and should probably be
        downgraded to match the most important road it actually connects
        to. If the way has no name, it's also likely a `_link` road
        (a ramp/connector) rather than a through route, so we prefer the
        `_link` variant of the guessed class when available.
        """
        neighbour_ranks = [
            r
            for r in (
                get_rank(hw)
                for hw in (
                    self.start.connecting_highways + self.end.connecting_highways
                )
            )
            if r is not None
        ]
        if not neighbour_ranks:
            return None

        # The best (most important / lowest numbered) connecting road found
        # at either terminus is our best guess for the way's true class.
        best_rank = min(neighbour_ranks)

        # Never suggest downgrading to something *less* important than what
        # we already found, and never "upgrade" past the way's own rank.
        best_rank = max(best_rank, 1)

        is_link = not self.name
        return rank_to_highway(best_rank, is_link=is_link)

    def josm_autofix_url(self) -> Optional[str]:
        """
        JOSM editor link that both loads the object and pre-fills the
        `addtags` parameter with the guessed `highway` tag fix, so the
        JOSM "Update" just needs to be confirmed (or edited) by the mapper.

        Returns None if no suggestion could be made (e.g. no valid
        connecting neighbours) or if the suggestion matches the current tag.
        """
        suggestion = self.suggested_highway()
        if not suggestion or suggestion == self.highway:
            return None
        return (
            f"http://localhost:8111/load_object?new_layer=false&objects=w{self.way_id}"
            f"&addtags=highway={suggestion}"
        )

    def to_dict(self) -> dict:
        return {
            "way_id": self.way_id,
            "name": self.name,
            "highway": self.highway,
            "rank": self.rank,
            "version": self.version,
            "changeset": self.changeset,
            "user": self.user,
            "timestamp": self.timestamp,
            # start terminus
            "start_node_id": self.start.node_id,
            "start_lat": self.start.lat,
            "start_lon": self.start.lon,
            "start_connecting_highways": ",".join(
                sorted(set(self.start.connecting_highways))
            ),
            "start_min_rank": self.start.min_connecting_rank,
            # end terminus
            "end_node_id": self.end.node_id,
            "end_lat": self.end.lat,
            "end_lon": self.end.lon,
            "end_connecting_highways": ",".join(
                sorted(set(self.end.connecting_highways))
            ),
            "end_min_rank": self.end.min_connecting_rank,
            # Editor links
            "osm_url": self.osm_url(),
            "josm_url": self.josm_url(),
            "id_url": self.id_url(),
            "level0_url": self.level0_url(),
            "suggested_highway": self.suggested_highway(),
            "josm_autofix_url": self.josm_autofix_url(),
        }


# ---------------------------------------------------------------------------
# Index builder
# ---------------------------------------------------------------------------


def build_terminus_index(
    ways: dict[int, WayRecord],
) -> dict[int, list[WayRecord]]:
    """
    Build an inverted index: node_id → list of WayRecords that contain that node.

    All nodes of each way are indexed, including intermediate nodes, so that
    we can find roads that connect at a terminus even if they meet in the
    middle of another way rather than at its endpoint.
    """
    index: dict[int, list[WayRecord]] = {}
    for way in ways.values():
        for node_id in way.node_ids:
            index.setdefault(node_id, []).append(way)
    return index


# ---------------------------------------------------------------------------
# Topology checker
# ---------------------------------------------------------------------------


def check_topology(
    ways: dict[int, WayRecord],
    node_coords: dict[int, NodeCoord],
) -> list[FlaggedWay]:
    """
    Main analysis function. Returns a list of FlaggedWay objects.

    A way is flagged when:
      1. Its highway type is in the analysed set (motorway → tertiary).
      2. BOTH termini have at least one connecting road (i.e. not a dead-end).
      3. Neither terminus has a connecting road of equal or higher rank.

    Roundabouts (closed ways where start_node == end_node) are skipped.
    """
    logger.info("Building terminus index from %d ways …", len(ways))
    index = build_terminus_index(ways)

    flagged: list[FlaggedWay] = []
    analysed_count = 0
    skipped_deadend = 0
    skipped_roundabout = 0
    skipped_ok = 0

    for way in ways.values():
        if not is_analysed(way.highway):
            continue

        analysed_count += 1

        # Skip roundabouts and other closed ways
        if way.start_node == way.end_node:
            skipped_roundabout += 1
            continue

        start_info = _evaluate_terminus(way, way.start_node, index, node_coords)
        end_info = _evaluate_terminus(way, way.end_node, index, node_coords)

        # Rule: skip if either terminus is a dead-end (no other roads at all)
        if not start_info.has_connections or not end_info.has_connections:
            skipped_deadend += 1
            continue

        # Rule: skip if either terminus already has a qualifying connection
        if start_info.has_qualifying_connection or end_info.has_qualifying_connection:
            skipped_ok += 1
            continue

        # Both termini are connected but only to lower-rank roads → flag it
        flagged.append(
            FlaggedWay(
                way_id=way.way_id,
                name=way.name,
                highway=way.highway,
                rank=way.rank,
                start=start_info,
                end=end_info,
                version=way.version,
                changeset=way.changeset,
                user=way.user,
                timestamp=way.timestamp,
            )
        )

    logger.info(
        "Analysis complete: %d ways checked | %d flagged | "
        "%d skipped (roundabout) | %d skipped (dead-end/boundary) | %d OK",
        analysed_count,
        len(flagged),
        skipped_roundabout,
        skipped_deadend,
        skipped_ok,
    )
    return flagged


def _evaluate_terminus(
    way: WayRecord,
    node_id: int,
    index: dict[int, list[WayRecord]],
    node_coords: dict[int, NodeCoord],
) -> TerminusInfo:
    """
    Evaluate connectivity at one terminus node of the given way.

    Excludes the way itself from the neighbour list so a way doesn't
    qualify itself.
    """
    coord = node_coords.get(node_id)
    neighbours = [w for w in index.get(node_id, []) if w.way_id != way.way_id]

    connecting_highways = [w.highway for w in neighbours]

    # Find the best (lowest = most important) rank among neighbours
    qualifying_ranks = [
        w.rank for w in neighbours if qualifies_as_upgrade(w.rank, way.rank)
    ]
    min_qualifying = min(qualifying_ranks) if qualifying_ranks else None

    return TerminusInfo(
        node_id=node_id,
        lat=coord.lat if coord else None,
        lon=coord.lon if coord else None,
        connecting_highways=connecting_highways,
        min_connecting_rank=min_qualifying,
    )
