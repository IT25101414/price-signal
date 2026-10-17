"""Tests for challenger_check.py: the adoption rule works on worlds with a known answer."""
import challenger_check as c


def test_linear_world_keeps_ridge():
    results, decision = c.run(c.synthetic(False), quiet=True)
    assert decision == "keep ridge"
    assert all(r["edge"] < c.MIN_EDGE for r in results if r["h"] == c.DECISION_H)


def test_threshold_world_adopts_boosted():
    results, decision = c.run(c.synthetic(True), quiet=True)
    assert decision == "ADOPT boosted"
    assert all(r["lo"] > 0 for r in results if r["h"] == c.DECISION_H)


def test_decide_needs_all_three_series():
    ok = dict(h=3, edge=0.02, lo=0.01)
    bad = dict(h=3, edge=0.02, lo=-0.01)
    assert c.decide([ok, ok, ok]) == "ADOPT boosted"
    assert c.decide([ok, ok, bad]) == "keep ridge"
    assert c.decide([ok, ok]).startswith("keep ridge")
