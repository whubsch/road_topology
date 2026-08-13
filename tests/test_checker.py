"""
Unit tests for the OSM highway hierarchy checker.

Run with:  pytest tests/
"""

from __future__ import annotations

import pytest

from road_topology.hierarchy import (
    get_rank,
    is_analysed,
    qualifies_as_upgrade,
)
from road_topology.checker import (
    FlaggedWay,
    build_terminus_index,
    check_topology,
)
from road_topology.parser import WayRecord, NodeCoord

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_way(
    way_id: int,
    highway: str,
    node_ids: list[int] | None = None,
) -> WayRecord:
    rank = get_rank(highway)
    assert rank is not None, f"Unknown highway: {highway}"
    return WayRecord(
        way_id=way_id,
        highway=highway,
        rank=rank,
        node_ids=node_ids or [way_id * 100, way_id * 100 + 1],
    )


def make_coord(node_id: int, lat: float = 51.5, lon: float = -0.1) -> NodeCoord:
    return NodeCoord(node_id=node_id, lat=lat, lon=lon)


# ---------------------------------------------------------------------------
# hierarchy.py
# ---------------------------------------------------------------------------


class TestHierarchy:
    def test_rank_ordering(self):
        assert get_rank("motorway") < get_rank("trunk")
        assert get_rank("trunk") < get_rank("primary")
        assert get_rank("primary") < get_rank("secondary")
        assert get_rank("secondary") < get_rank("tertiary")
        assert get_rank("tertiary") < get_rank("unclassified")
        assert get_rank("unclassified") == get_rank("residential")

    def test_link_roads_same_rank_as_parent(self):
        assert get_rank("motorway_link") == get_rank("motorway")
        assert get_rank("trunk_link") == get_rank("trunk")
        assert get_rank("primary_link") == get_rank("primary")
        assert get_rank("secondary_link") == get_rank("secondary")
        assert get_rank("tertiary_link") == get_rank("tertiary")

    def test_unknown_highway_returns_none(self):
        assert get_rank("proposed") is None
        assert get_rank("construction") is None
        assert get_rank("") is None

    def test_is_analysed(self):
        for hw in [
            "motorway",
            "motorway_link",
            "trunk",
            "primary",
            "secondary",
            "tertiary",
            "tertiary_link",
        ]:
            assert is_analysed(hw), f"{hw} should be analysed"

    def test_is_not_analysed(self):
        for hw in ["unclassified", "residential", "service", "track", "path"]:
            assert not is_analysed(hw), f"{hw} should NOT be analysed"

    def test_qualifies_as_upgrade_equal(self):
        """Equal rank always qualifies."""
        assert qualifies_as_upgrade(3, 3)  # primary → primary

    def test_qualifies_as_upgrade_higher(self):
        """Lower rank number = more important = qualifies."""
        assert qualifies_as_upgrade(1, 5)  # motorway → tertiary: qualifies
        assert qualifies_as_upgrade(2, 3)  # trunk → primary: qualifies

    def test_does_not_qualify_lower(self):
        """Higher rank number = less important = does not qualify."""
        assert not qualifies_as_upgrade(5, 3)  # tertiary → primary: doesn't qualify
        assert not qualifies_as_upgrade(6, 3)  # residential → primary: doesn't qualify


# ---------------------------------------------------------------------------
# checker.py — build_terminus_index
# ---------------------------------------------------------------------------


class TestTerminusIndex:
    def test_basic_index(self):
        w1 = make_way(1, "primary", [100, 101, 102])
        w2 = make_way(2, "secondary", [102, 103, 104])
        index = build_terminus_index({1: w1, 2: w2})

        # Node 102 is the end of w1 and start of w2
        assert 102 in index
        way_ids = {w.way_id for w in index[102]}
        assert way_ids == {1, 2}

    def test_isolated_way(self):
        w = make_way(1, "tertiary", [10, 11])
        index = build_terminus_index({1: w})
        assert set(index.keys()) == {10, 11}

    def test_node_appears_in_multiple_ways(self):
        shared_node = 999
        ways = {i: make_way(i, "secondary", [shared_node, i * 10]) for i in range(1, 6)}
        index = build_terminus_index(ways)
        assert len(index[shared_node]) == 5


# ---------------------------------------------------------------------------
# checker.py — check_topology (integration-style)
# ---------------------------------------------------------------------------


class TestCheckTopology:
    def _run(
        self,
        ways: dict[int, WayRecord],
        node_coords: dict[int, NodeCoord] | None = None,
    ) -> list[FlaggedWay]:
        coords = node_coords or {}
        return check_topology(ways, coords)

    # ── Should be flagged ──────────────────────────────────────────────────

    def test_primary_surrounded_by_residential_flagged(self):
        """
        primary ──[A]──── primary_way ────[B]──
                  |                            |
               residential                 residential

        The primary way connects only to residential at both ends → flag it.
        """
        node_A, node_B = 1, 2
        primary_way = make_way(10, "primary", [node_A, node_B])
        res_a = make_way(20, "residential", [node_A, 100])
        res_b = make_way(30, "residential", [node_B, 101])

        ways = {10: primary_way, 20: res_a, 30: res_b}
        flagged = self._run(ways)

        assert len(flagged) == 1
        assert flagged[0].way_id == 10

    def test_secondary_surrounded_by_tertiary_flagged(self):
        node_A, node_B = 1, 2
        sec = make_way(10, "secondary", [node_A, node_B])
        tert_a = make_way(20, "tertiary", [node_A, 100])
        tert_b = make_way(30, "tertiary", [node_B, 101])

        ways = {10: sec, 20: tert_a, 30: tert_b}
        flagged = self._run(ways)
        assert any(f.way_id == 10 for f in flagged)

    # ── Should NOT be flagged ──────────────────────────────────────────────

    def test_dead_end_not_flagged(self):
        """One terminus has no connecting way → skip (boundary/cul-de-sac rule)."""
        node_A, node_B = 1, 2
        primary_way = make_way(10, "primary", [node_A, node_B])
        res_a = make_way(20, "residential", [node_A, 100])
        # node_B has no other road

        ways = {10: primary_way, 20: res_a}
        flagged = self._run(ways)
        assert not flagged

    def test_primary_connecting_to_trunk_not_flagged(self):
        node_A, node_B = 1, 2
        primary_way = make_way(10, "primary", [node_A, node_B])
        trunk = make_way(20, "trunk", [node_A, 100])  # higher rank at A
        residential = make_way(30, "residential", [node_B, 101])  # lower at B

        ways = {10: primary_way, 20: trunk, 30: residential}
        flagged = self._run(ways)
        # start has trunk (rank 2 ≤ 3) → qualifies → not flagged
        assert not any(f.way_id == 10 for f in flagged)

    def test_primary_connecting_to_another_primary_not_flagged(self):
        node_A, node_B = 1, 2
        p1 = make_way(10, "primary", [node_A, node_B])
        p2 = make_way(20, "primary", [node_A, 100])  # equal rank at A
        res = make_way(30, "residential", [node_B, 101])

        ways = {10: p1, 20: p2, 30: res}
        flagged = self._run(ways)
        assert not any(f.way_id == 10 for f in flagged)

    def test_residential_not_analysed(self):
        """Residential ways should never appear in flagged output."""
        node_A, node_B = 1, 2
        res = make_way(10, "residential", [node_A, node_B])
        unclass = make_way(20, "unclassified", [node_A, 100])
        service = make_way(30, "service", [node_B, 101])

        ways = {10: res, 20: unclass, 30: service}
        flagged = self._run(ways)
        assert not any(f.way_id == 10 for f in flagged)

    def test_motorway_link_treated_as_motorway_rank(self):
        """motorway_link connecting to motorway should satisfy the rule."""
        node_A, node_B = 1, 2
        link = make_way(10, "motorway_link", [node_A, node_B])
        mway = make_way(20, "motorway", [node_A, 100])
        res = make_way(30, "residential", [node_B, 101])

        ways = {10: link, 20: mway, 30: res}
        flagged = self._run(ways)
        assert not any(f.way_id == 10 for f in flagged)

    def test_both_ends_dead_end_not_flagged(self):
        """An isolated way with no neighbours at all is skipped."""
        isolated = make_way(10, "primary", [1, 2])
        flagged = self._run({10: isolated})
        assert not flagged

    # ── Output structure ───────────────────────────────────────────────────

    def test_flagged_way_to_dict_keys(self):
        node_A, node_B = 1, 2
        coords = {
            node_A: make_coord(node_A, 51.5, -0.1),
            node_B: make_coord(node_B, 51.6, -0.2),
        }
        primary_way = make_way(10, "primary", [node_A, node_B])
        res_a = make_way(20, "residential", [node_A, 100])
        res_b = make_way(30, "residential", [node_B, 101])

        ways = {10: primary_way, 20: res_a, 30: res_b}
        flagged = self._run(ways, coords)
        assert flagged

        d = flagged[0].to_dict()
        for key in [
            "way_id",
            "highway",
            "rank",
            "start_node_id",
            "start_lat",
            "start_lon",
            "end_node_id",
            "end_lat",
            "end_lon",
            "josm_url",
        ]:
            assert key in d, f"Missing key: {key}"

    def test_coordinates_attached_to_flagged_way(self):
        node_A, node_B = 1, 2
        coords = {
            node_A: make_coord(node_A, 48.85, 2.35),
            node_B: make_coord(node_B, 48.86, 2.36),
        }
        primary_way = make_way(10, "primary", [node_A, node_B])
        res_a = make_way(20, "residential", [node_A, 100])
        res_b = make_way(30, "residential", [node_B, 101])

        ways = {10: primary_way, 20: res_a, 30: res_b}
        flagged = self._run(ways, coords)

        assert flagged[0].start.lat == pytest.approx(48.85)
        assert flagged[0].end.lon == pytest.approx(2.36)
