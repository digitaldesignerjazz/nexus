#!/usr/bin/env python3
"""
Unit Tests for Hyperspace Link Quality Oracle (M11)

Covers:
- Initialization and configuration
- Link update mechanics (dict + dataclass)
- EWMA smoothing correctness
- Composite quality scoring + bounds
- Emotional resonance modulation (positive/negative/fatigue)
- Flap detection and status transitions
- Trend detection
- Query methods (score, report, rank, summary)
- Edge cases (missing links, first sample, extremes)

Run with:
    python -m pytest python/tests/test_hyperspace_link_quality_oracle.py -v
or
    python python/tests/test_hyperspace_link_quality_oracle.py

Designed to validate the oracle as a reliable advisor for NexusOrchestrator
and emotional agent swarms.
"""

import unittest
from dataclasses import asdict

from hyperspace_link_quality_oracle import (
    HyperspaceLinkQualityOracle,
    LinkMetrics,
    LinkStatus,
    LinkHealthReport,
)


class TestHyperspaceLinkQualityOracle(unittest.TestCase):
    """Comprehensive test suite for the Hyperspace Link Quality Oracle."""

    def setUp(self):
        """Fresh oracle instance for each test with predictable parameters."""
        self.oracle = HyperspaceLinkQualityOracle(
            ewma_alpha=0.3,
            history_window=10,
            flap_threshold=3
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
        self.assertEqual(report.ewma_latency, 30.0)  # first sample

    # === EWMA Smoothing ===
    def test_ewma_smoothing_behavior(self):
        # First update
        self.oracle.update_link(self.link_id, {"latency_ms": 100.0, "packet_loss": 0.0})
        # Second update with lower latency
        report = self.oracle.update_link(self.link_id, {"latency_ms": 40.0, "packet_loss": 0.0})

        # EWMA should be between 40 and 100, closer to 40 with alpha=0.3
        self.assertGreater(report.ewma_latency, 40)
        self.assertLess(report.ewma_latency, 100)
        # More precisely: 0.3*40 + 0.7*100 = 82
        self.assertAlmostEqual(report.ewma_latency, 82.0, delta=0.1)

    # === Quality Score ===
    def test_quality_score_bounds(self):
        # Excellent link
        report = self.oracle.update_link("good-link", {"latency_ms": 5.0, "packet_loss": 0.0})
        self.assertGreaterEqual(report.quality_score, 85)

        # Terrible link
        bad_report = self.oracle.update_link("bad-link", {"latency_ms": 300.0, "packet_loss": 0.4})
        self.assertLessEqual(bad_report.quality_score, 40)

    def test_quality_score_emotional_boost(self):
        base = self.oracle.update_link("emo-test", {"latency_ms": 50.0, "packet_loss": 0.02})
        base_score = base.quality_score

        # High positive resonance should increase score
        boosted = self.oracle.update_link(
            "emo-test",
            {"latency_ms": 50.0, "packet_loss": 0.02},
            emotional_state={"resonance": 0.9, "fatigue": 0.0, "loyalty": 0.8}
        )
        self.assertGreater(boosted.quality_score, base_score)

    def test_quality_score_emotional_penalty(self):
        base = self.oracle.update_link("emo-penalty", {"latency_ms": 50.0, "packet_loss": 0.02})
        base_score = base.quality_score

        penalized = self.oracle.update_link(
            "emo-penalty",
            {"latency_ms": 50.0, "packet_loss": 0.02},
            emotional_state={"resonance": 0.1, "fatigue": 0.8, "loyalty": 0.3}
        )
        self.assertLess(penalized.quality_score, base_score)

    # === Flap Detection & Status ===
    def test_flap_detection(self):
        link = "flappy-link"
        # Start stable
        self.oracle.update_link(link, {"latency_ms": 30.0, "packet_loss": 0.01})

        # Cause several large jumps (simulating flaps)
        for latency in [80, 25, 95, 20, 110]:
            self.oracle.update_link(link, {"latency_ms": latency, "packet_loss": 0.01})

        report = self.oracle.get_detailed_report(link)
        self.assertEqual(report.status, LinkStatus.FLAPPING)
        self.assertGreaterEqual(report.flap_count, self.oracle.flap_threshold)

    def test_status_transitions(self):
        link = "status-link"
        r1 = self.oracle.update_link(link, {"latency_ms": 20.0, "packet_loss": 0.0})
        self.assertEqual(r1.status, LinkStatus.STABLE)

        # Degrade it
        r2 = self.oracle.update_link(link, {"latency_ms": 180.0, "packet_loss": 0.25})
        self.assertIn(r2.status, (LinkStatus.DEGRADED, LinkStatus.FLAPPING))

    def test_resonant_status(self):
        link = "resonant-link"
        self.oracle.update_link(
            link,
            {"latency_ms": 15.0, "packet_loss": 0.005},
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
        self.assertEqual(ranked[0][0], "best")  # highest first
        self.assertGreater(ranked[0][1], ranked[-1][1])

    def test_oracle_summary(self):
        self.oracle.update_link("l1", {"latency_ms": 25.0, "packet_loss": 0.01})
        self.oracle.update_link("l2", {"latency_ms": 120.0, "packet_loss": 0.2})

        summary = self.oracle.get_oracle_summary()
        self.assertEqual(summary["total_links"], 2)
        self.assertIn("average_quality", summary)
        self.assertGreaterEqual(summary["healthy_count"], 0)

    # === Trend ===
    def test_trend_detection(self):
        link = "trend-link"
        # Improving trend
        for lat in [100, 80, 55, 30]:
            self.oracle.update_link(link, {"latency_ms": lat, "packet_loss": 0.01})
        report = self.oracle.get_detailed_report(link)
        self.assertEqual(report.trend, "improving")

    # === Edge Cases ===
    def test_extreme_values(self):
        report = self.oracle.update_link(
            "extreme",
            {"latency_ms": 9999.0, "packet_loss": 0.99}
        )
        self.assertGreaterEqual(report.quality_score, 0.0)
        self.assertLessEqual(report.quality_score, 100.0)

    def test_emotional_resonance_bounds(self):
        self.oracle.update_link(
            self.link_id,
            {"latency_ms": 40.0},
            emotional_state={"resonance": 10.0, "fatigue": -5.0}  # out of range
        )
        report = self.oracle.get_detailed_report(self.link_id)
        self.assertGreaterEqual(report.emotional_resonance, -1.0)
        self.assertLessEqual(report.emotional_resonance, 1.0)

    def test_modulate_by_emotional_core(self):
        self.oracle.update_link(self.link_id, {"latency_ms": 50.0})
        self.oracle.modulate_by_emotional_core(
            self.link_id, {"resonance": 0.7, "fatigue": 0.2}
        )
        report = self.oracle.get_detailed_report(self.link_id)
        self.assertGreater(report.emotional_resonance, 0.3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
