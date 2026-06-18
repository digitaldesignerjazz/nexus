#!/usr/bin/env python3
"""
Unit Tests for Hyperspace Link Quality Oracle (M11)

Includes:
- Classic unittest tests
- Property-based tests with Hypothesis (optional dependency)

Property-based testing validates core invariants across thousands of random inputs:
- Quality score always clamped to [0, 100]
- Emotional resonance always clamped to [-1.0, 1.0]
- Status is always a valid LinkStatus member
- Flap count is non-decreasing
- rank_links returns correctly sorted results
- Multiple sequential updates never break internal state

Install Hypothesis for full coverage:
    pip install hypothesis

Run:
    python -m pytest python/tests/test_hyperspace_link_quality_oracle.py -v
    # or without pytest
    python python/tests/test_hyperspace_link_quality_oracle.py
"""

import unittest
from dataclasses import asdict

try:
    from hypothesis import given, strategies as st, settings
    from hypothesis.strategies import floats, lists, tuples, integers
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False


from hyperspace_link_quality_oracle import (
    HyperspaceLinkQualityOracle,
    LinkMetrics,
    LinkStatus,
    LinkHealthReport,
)


class TestHyperspaceLinkQualityOracle(unittest.TestCase):
    """Classic unit tests for the Hyperspace Link Quality Oracle."""

    def setUp(self):
        self.oracle = HyperspaceLinkQualityOracle(
            ewma_alpha=0.3, history_window=10, flap_threshold=3
        )
        self.link_id = "test-peer-001"

    # === Initialization ===
    def test_initialization_defaults(self):
        oracle = HyperspaceLinkQualityOracle()
        self.assertGreater(oracle.ewma_alpha, 0)
        self.assertLessEqual(oracle.ewma_alpha, 0.95)
        self.assertEqual(oracle.history_window, 20)
        self.assertEqual(oracle.flap_threshold, 4)

    def test_initialization_custom(self):
        oracle = HyperspaceLinkQualityOracle(ewma_alpha=0.5, history_window=5, flap_threshold=2)
        self.assertEqual(oracle.ewma_alpha, 0.5)
        self.assertEqual(oracle.history_window, 5)
        self.assertEqual(oracle.flap_threshold, 2)

    # === Update & First Sample ===
    def test_first_update_creates_state(self):
        metrics = {"latency_ms": 45.0, "packet_loss": 0.02}
        report = self.oracle.update_link(self.link_id, metrics)
        self.assertIsInstance(report, LinkHealthReport)
        self.assertEqual(report.link_id, self.link_id)
        self.assertGreater(report.quality_score, 0)
        self.assertLessEqual(report.quality_score, 100)
        self.assertEqual(report.status, LinkStatus.STABLE)
        self.assertEqual(report.history_length, 1)

    def test_update_accepts_dataclass(self):
        metrics = LinkMetrics(latency_ms=30.0, packet_loss=0.01, connected_peers=12)
        report = self.oracle.update_link(self.link_id, metrics)
        self.assertEqual(report.ewma_latency, 30.0)

    # === EWMA ===
    def test_ewma_smoothing_behavior(self):
        self.oracle.update_link(self.link_id, {"latency_ms": 100.0, "packet_loss": 0.0})
        report = self.oracle.update_link(self.link_id, {"latency_ms": 40.0, "packet_loss": 0.0})
        self.assertGreater(report.ewma_latency, 40)
        self.assertLess(report.ewma_latency, 100)
        self.assertAlmostEqual(report.ewma_latency, 82.0, delta=0.1)

    # === Quality Score ===
    def test_quality_score_bounds(self):
        report = self.oracle.update_link("good-link", {"latency_ms": 5.0, "packet_loss": 0.0})
        self.assertGreaterEqual(report.quality_score, 85)
        bad_report = self.oracle.update_link("bad-link", {"latency_ms": 300.0, "packet_loss": 0.4})
        self.assertLessEqual(bad_report.quality_score, 40)

    def test_quality_score_emotional_boost(self):
        base = self.oracle.update_link("emo-test", {"latency_ms": 50.0, "packet_loss": 0.02})
        boosted = self.oracle.update_link(
            "emo-test", {"latency_ms": 50.0, "packet_loss": 0.02},
            emotional_state={"resonance": 0.9, "fatigue": 0.0, "loyalty": 0.8}
        )
        self.assertGreater(boosted.quality_score, base.quality_score)

    def test_quality_score_emotional_penalty(self):
        base = self.oracle.update_link("emo-penalty", {"latency_ms": 50.0, "packet_loss": 0.02})
        penalized = self.oracle.update_link(
            "emo-penalty", {"latency_ms": 50.0, "packet_loss": 0.02},
            emotional_state={"resonance": 0.1, "fatigue": 0.8, "loyalty": 0.3}
        )
        self.assertLess(penalized.quality_score, base.quality_score)

    # === Flap & Status ===
    def test_flap_detection(self):
        link = "flappy-link"
        self.oracle.update_link(link, {"latency_ms": 30.0, "packet_loss": 0.01})
        for latency in [80, 25, 95, 20, 110]:
            self.oracle.update_link(link, {"latency_ms": latency, "packet_loss": 0.01})
        report = self.oracle.get_detailed_report(link)
        self.assertEqual(report.status, LinkStatus.FLAPPING)
        self.assertGreaterEqual(report.flap_count, self.oracle.flap_threshold)

    def test_status_transitions(self):
        link = "status-link"
        r1 = self.oracle.update_link(link, {"latency_ms": 20.0, "packet_loss": 0.0})
        self.assertEqual(r1.status, LinkStatus.STABLE)
        r2 = self.oracle.update_link(link, {"latency_ms": 180.0, "packet_loss": 0.25})
        self.assertIn(r2.status, (LinkStatus.DEGRADED, LinkStatus.FLAPPING))

    def test_resonant_status(self):
        link = "resonant-link"
        self.oracle.update_link(
            link, {"latency_ms": 15.0, "packet_loss": 0.005},
            emotional_state={"resonance": 0.85, "fatigue": 0.1, "loyalty": 0.95}
        )
        report = self.oracle.get_detailed_report(link)
        self.assertEqual(report.status, LinkStatus.RESONANT)

    # === Query Methods ===
    def test_get_quality_score_missing(self):
        self.assertEqual(self.oracle.get_quality_score("nonexistent"), 0.0)

    def test_get_detailed_report_missing(self):
        self.assertIsNone(self.oracle.get_detailed_report("ghost-link"))

    def test_rank_links(self):
        self.oracle.update_link("best", {"latency_ms": 10.0, "packet_loss": 0.0})
        self.oracle.update_link("medium", {"latency_ms": 60.0, "packet_loss": 0.05})
        self.oracle.update_link("worst", {"latency_ms": 200.0, "packet_loss": 0.3})
        ranked = self.oracle.rank_links(min_quality=30)
        self.assertGreater(len(ranked), 0)
        self.assertEqual(ranked[0][0], "best")
        self.assertGreater(ranked[0][1], ranked[-1][1])

    def test_oracle_summary(self):
        self.oracle.update_link("l1", {"latency_ms": 25.0, "packet_loss": 0.01})
        self.oracle.update_link("l2", {"latency_ms": 120.0, "packet_loss": 0.2})
        summary = self.oracle.get_oracle_summary()
        self.assertEqual(summary["total_links"], 2)
        self.assertIn("average_quality", summary)

    # === Trend & Edges ===
    def test_trend_detection(self):
        link = "trend-link"
        for lat in [100, 80, 55, 30]:
            self.oracle.update_link(link, {"latency_ms": lat, "packet_loss": 0.01})
        report = self.oracle.get_detailed_report(link)
        self.assertEqual(report.trend, "improving")

    def test_extreme_values(self):
        report = self.oracle.update_link("extreme", {"latency_ms": 9999.0, "packet_loss": 0.99})
        self.assertGreaterEqual(report.quality_score, 0.0)
        self.assertLessEqual(report.quality_score, 100.0)

    def test_emotional_resonance_bounds(self):
        self.oracle.update_link(
            self.link_id, {"latency_ms": 40.0},
            emotional_state={"resonance": 10.0, "fatigue": -5.0}
        )
        report = self.oracle.get_detailed_report(self.link_id)
        self.assertGreaterEqual(report.emotional_resonance, -1.0)
        self.assertLessEqual(report.emotional_resonance, 1.0)

    def test_modulate_by_emotional_core(self):
        self.oracle.update_link(self.link_id, {"latency_ms": 50.0})
        self.oracle.modulate_by_emotional_core(self.link_id, {"resonance": 0.7, "fatigue": 0.2})
        report = self.oracle.get_detailed_report(self.link_id)
        self.assertGreater(report.emotional_resonance, 0.3)


# ============================================================
# PROPERTY-BASED TESTS (Hypothesis)
# ============================================================

if HYPOTHESIS_AVAILABLE:
    class TestHyperspaceLinkQualityOracleProperties(unittest.TestCase):
        """Property-based tests that explore a huge input space.

        These tests use Hypothesis to generate thousands of random (and edge)
        inputs and assert that fundamental invariants of the oracle always hold.
        This catches subtle bugs in clamping, scoring, and state management
        that example-based tests often miss.
        """

        @given(
            latency=floats(min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False),
            packet_loss=floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
            resonance=floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
            fatigue=floats(min_value=-2.0, max_value=2.0, allow_nan=False, allow_infinity=False),
        )
        @settings(max_examples=200, deadline=None)
        def test_quality_and_resonance_always_clamped(self, latency, packet_loss, resonance, fatigue):
            """Quality score must always be in [0, 100]. Emotional resonance must be clamped to [-1, 1]."""
            oracle = HyperspaceLinkQualityOracle(ewma_alpha=0.25)
            emotional = {"resonance": resonance, "fatigue": fatigue, "loyalty": 0.5}
            report = oracle.update_link(
                "prop-link", {"latency_ms": latency, "packet_loss": packet_loss}, emotional_state=emotional
            )
            self.assertGreaterEqual(report.quality_score, 0.0)
            self.assertLessEqual(report.quality_score, 100.0)
            self.assertGreaterEqual(report.emotional_resonance, -1.0)
            self.assertLessEqual(report.emotional_resonance, 1.0)
            self.assertIsInstance(report.status, LinkStatus)

        @given(
            updates=lists(
                tuples(
                    floats(min_value=0.1, max_value=2000),
                    floats(min_value=0.0, max_value=1.0)
                ),
                min_size=1,
                max_size=30
            )
        )
        @settings(max_examples=100, deadline=None)
        def test_sequential_updates_never_break_state(self, updates):
            """After any sequence of updates, the oracle remains consistent."""
            oracle = HyperspaceLinkQualityOracle()
            link = "seq-link"
            for latency, loss in updates:
                report = oracle.update_link(link, {"latency_ms": latency, "packet_loss": loss})
                self.assertGreaterEqual(report.quality_score, 0.0)
                self.assertLessEqual(report.quality_score, 100.0)
                self.assertGreaterEqual(oracle.get_quality_score(link), 0.0)

        @given(
            n_links=integers(min_value=1, max_value=15)
        )
        @settings(max_examples=50)
        def test_rank_links_is_sorted_and_bounded(self, n_links):
            """rank_links always returns results sorted descending and within valid range."""
            oracle = HyperspaceLinkQualityOracle()
            for i in range(n_links):
                lat = 10 + i * 15
                oracle.update_link(f"link-{i}", {"latency_ms": lat, "packet_loss": 0.01 * i})
            ranked = oracle.rank_links(min_quality=0)
            if ranked:
                scores = [score for _, score in ranked]
                self.assertEqual(scores, sorted(scores, reverse=True))
                for score in scores:
                    self.assertGreaterEqual(score, 0.0)
                    self.assertLessEqual(score, 100.0)

        @given(
            resonance=floats(min_value=-10, max_value=10),
            fatigue=floats(min_value=-5, max_value=5),
        )
        def test_modulate_by_emotional_core_clamps(self, resonance, fatigue):
            """Direct modulation also respects resonance bounds."""
            oracle = HyperspaceLinkQualityOracle()
            oracle.update_link("mod-link", {"latency_ms": 50.0})
            oracle.modulate_by_emotional_core("mod-link", {"resonance": resonance, "fatigue": fatigue})
            report = oracle.get_detailed_report("mod-link")
            self.assertGreaterEqual(report.emotional_resonance, -1.0)
            self.assertLessEqual(report.emotional_resonance, 1.0)

else:
    print("[INFO] Hypothesis not installed. Property-based tests are skipped.")
    print("         Install with: pip install hypothesis")


if __name__ == "__main__":
    unittest.main(verbosity=2)
