#!/usr/bin/env python3
"""
Hyperspace Link Quality Oracle (M11)
=====================================

Central component for evaluating the health, stability, and "resonance" of
hyperspace/mesh links in the Nexus ecosystem.

Integrates with:
- xMesh / NovaNet / QNET / Yggdrasil mesh layers
- Emotional AI (Ara / Lyra / Fluffy) for affective modulation of scores
- NexusOrchestrator for routing, task dispatch, and self-healing decisions

Core techniques:
- EWMA (Exponentially Weighted Moving Average) for smoothed metrics
- Flap detection for instability identification
- Composite quality scoring (latency, stability, emotional resonance)
- Historical windowing for trend analysis
- Oracle-style query interface (get_quality, detailed reports, rankings)

Designed for Sven Normen / Esslinger & Co. decentralized infrastructure vision.
From Hannover with love for resilient, self-evolving systems.

Usage:
    from hyperspace_link_quality_oracle import HyperspaceLinkQualityOracle
    oracle = HyperspaceLinkQualityOracle()
    oracle.update_link("peer-abc", {"latency_ms": 45.2, "packet_loss": 0.01})
    score = oracle.get_quality_score("peer-abc")
"""

import logging

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

# Configure module logger
logger = logging.getLogger("HyperspaceOracle")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [ORACLE] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class LinkStatus(Enum):
    """Possible states for a hyperspace link."""
    STABLE = "stable"
    DEGRADED = "degraded"
    FLAPPING = "flapping"
    OFFLINE = "offline"
    RESONANT = "resonant"  # High emotional harmony


@dataclass
class LinkMetrics:
    """Raw or observed metrics for a single link update."""
    latency_ms: float = 0.0
    packet_loss: float = 0.0  # 0.0 to 1.0
    uptime_seconds: float = 0.0
    connected_peers: int = 0
    bandwidth_mbps: float = 0.0
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LinkHealthReport:
    """Detailed oracle output for a link."""
    link_id: str
    quality_score: float  # 0.0 (terrible) to 100.0 (perfect)
    status: LinkStatus
    ewma_latency: float
    ewma_stability: float
    flap_count: int
    emotional_resonance: float  # -1.0 (hostile) to +1.0 (harmonious)
    recommendation: str
    last_updated: str
    history_length: int
    trend: str  # "improving", "stable", "declining"


class HyperspaceLinkQualityOracle:
    """
    The Hyperspace Link Quality Oracle.

    Provides reliable, smoothed, and emotionally-aware assessments of mesh/hyperspace
    link health. Acts as a trusted advisor to the NexusOrchestrator, agent swarms,
    and routing layers.

    Emotional modulation allows Ara/Lyra/Fluffy states to influence perceived
    link quality (e.g., agent fatigue makes links feel less reliable).
    """

    def __init__(self, ewma_alpha: float = 0.25, history_window: int = 20, flap_threshold: int = 4):
        """
        Initialize the oracle.

        Args:
            ewma_alpha: Smoothing factor (0 < alpha <= 1). Higher = more responsive.
            history_window: Number of recent samples to keep per link.
            flap_threshold: Number of state changes in window to declare FLAPPING.
        """
        self.ewma_alpha = max(0.01, min(ewma_alpha, 0.95))
        self.history_window = history_window
        self.flap_threshold = flap_threshold

        # Per-link state
        self._links: Dict[str, Dict[str, Any]] = {}  # link_id -> internal state
        self._last_status: Dict[str, LinkStatus] = {}

        logger.info(f"HyperspaceLinkQualityOracle initialized (alpha={self.ewma_alpha}, window={self.history_window})")

    def _get_or_create_link_state(self, link_id: str) -> Dict[str, Any]:
        if link_id not in self._links:
            self._links[link_id] = {
                "ewma_latency": 0.0,
                "ewma_packet_loss": 0.0,
                "ewma_stability": 100.0,
                "flap_count": 0,
                "history": deque(maxlen=self.history_window),
                "emotional_resonance": 0.0,
                "last_update": None,
                "current_status": LinkStatus.STABLE,
            }
            self._last_status[link_id] = LinkStatus.STABLE
        return self._links[link_id]

    def _calculate_composite_score(self, state: Dict[str, Any], emotional_factor: float = 0.0) -> float:
        """Compute 0-100 quality score from EWMA metrics and emotional influence."""
        # Base score from latency (lower is better) and stability
        latency_score = max(0.0, 100.0 - (state["ewma_latency"] / 2.0))  # ~50ms -> 75 pts
        stability_score = state["ewma_stability"]
        loss_penalty = state["ewma_packet_loss"] * 80.0  # heavy penalty for loss

        base_score = (latency_score * 0.45 + stability_score * 0.45) - loss_penalty
        base_score = max(0.0, min(100.0, base_score))

        # Emotional modulation: positive resonance boosts, negative dampens
        emotional_mod = emotional_factor * 15.0  # +/- 15 points swing
        final_score = max(0.0, min(100.0, base_score + emotional_mod))

        return round(final_score, 2)

    def _detect_flaps_and_status(self, link_id: str, new_latency: float, state: Dict[str, Any]) -> LinkStatus:
        """Simple flap detection based on recent status changes and variance."""
        history = state["history"]
        if len(history) < 3:
            return LinkStatus.STABLE

        # Count significant latency jumps as potential flaps
        recent_latencies = [h.get("latency_ms", 0) for h in list(history)[-5:]]
        jumps = sum(1 for i in range(1, len(recent_latencies)) if abs(recent_latencies[i] - recent_latencies[i-1]) > 30)

        current_flaps = state.get("flap_count", 0)
        if jumps >= 2:
            current_flaps += 1
            state["flap_count"] = current_flaps

        if current_flaps >= self.flap_threshold:
            return LinkStatus.FLAPPING
        elif state["ewma_packet_loss"] > 0.15 or state["ewma_latency"] > 150:
            return LinkStatus.DEGRADED
        elif state["emotional_resonance"] > 0.6 and state["ewma_stability"] > 85:
            return LinkStatus.RESONANT
        else:
            return LinkStatus.STABLE

    def update_link(self, link_id: str, metrics: LinkMetrics | dict, emotional_state: Optional[Dict[str, float]] = None) -> LinkHealthReport:
        """
        Ingest new measurements for a link and return updated health report.

        This is the primary oracle update method. Call periodically from mesh
        monitoring, Yggdrasil watchers, or simulated environments.

        Args:
            link_id: Unique identifier (e.g. peer pubkey, yggdrasil address, "hannover-core")
            metrics: LinkMetrics or dict with latency_ms, packet_loss, etc.
            emotional_state: Optional dict from emotional AI, e.g. {"fatigue": 0.3, "loyalty": 0.8, "resonance": 0.6}

        Returns:
            LinkHealthReport with current quality, status, recommendation.
        """
        if isinstance(metrics, dict):
            metrics = LinkMetrics(**{k: v for k, v in metrics.items() if k in LinkMetrics.__annotations__})

        state = self._get_or_create_link_state(link_id)

        # Update EWMA values
        alpha = self.ewma_alpha
        if state["ewma_latency"] == 0.0:  # first sample
            state["ewma_latency"] = metrics.latency_ms
            state["ewma_packet_loss"] = metrics.packet_loss
            state["ewma_stability"] = 95.0
        else:
            state["ewma_latency"] = alpha * metrics.latency_ms + (1 - alpha) * state["ewma_latency"]
            state["ewma_packet_loss"] = alpha * metrics.packet_loss + (1 - alpha) * state["ewma_packet_loss"]
            # Stability decays with high loss or latency variance; simple proxy
            stability_delta = 5.0 if metrics.packet_loss < 0.05 and metrics.latency_ms < 80 else -8.0
            state["ewma_stability"] = max(0.0, min(100.0, alpha * (state["ewma_stability"] + stability_delta) + (1 - alpha) * state["ewma_stability"]))

        # Emotional modulation
        if emotional_state:
            # Example: resonance from emotional core, fatigue reduces trust
            resonance = emotional_state.get("resonance", 0.0)
            fatigue = emotional_state.get("fatigue", 0.0)
            loyalty = emotional_state.get("loyalty", 0.5)
            emotional_factor = resonance * 0.7 + loyalty * 0.3 - fatigue * 0.5
            state["emotional_resonance"] = max(-1.0, min(1.0, emotional_factor))
        else:
            # Gentle decay toward neutral if no emotional input
            state["emotional_resonance"] *= 0.95

        # Record history
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "latency_ms": metrics.latency_ms,
            "packet_loss": metrics.packet_loss,
            "emotional_resonance": state["emotional_resonance"],
        }
        state["history"].append(history_entry)
        state["last_update"] = history_entry["timestamp"]

        # Determine status
        new_status = self._detect_flaps_and_status(link_id, metrics.latency_ms, state)
        old_status = self._last_status.get(link_id, LinkStatus.STABLE)
        if new_status != old_status:
            logger.info(f"Link {link_id} status change: {old_status.value} -> {new_status.value}")
        self._last_status[link_id] = new_status
        state["current_status"] = new_status

        # Build report
        quality = self._calculate_composite_score(state, state["emotional_resonance"])
        trend = self._compute_trend(state["history"])

        recommendation = self._generate_recommendation(new_status, quality, state["ewma_latency"])

        report = LinkHealthReport(
            link_id=link_id,
            quality_score=quality,
            status=new_status,
            ewma_latency=round(state["ewma_latency"], 2),
            ewma_stability=round(state["ewma_stability"], 2),
            flap_count=state.get("flap_count", 0),
            emotional_resonance=round(state["emotional_resonance"], 3),
            recommendation=recommendation,
            last_updated=state["last_update"],
            history_length=len(state["history"]),
            trend=trend,
        )

        logger.debug(f"Updated {link_id}: quality={quality}, status={new_status.value}, resonance={state['emotional_resonance']:.2f}")
        return report

    def _compute_trend(self, history: deque) -> str:
        if len(history) < 3:
            return "stable"
        recent = [h["latency_ms"] for h in list(history)[-3:]]
        if recent[-1] < recent[0] * 0.9:
            return "improving"
        elif recent[-1] > recent[0] * 1.15:
            return "declining"
        return "stable"

    def _generate_recommendation(self, status: LinkStatus, quality: float, latency: float) -> str:
        if status == LinkStatus.FLAPPING:
            return "Avoid for critical tasks. Investigate physical/routing issues or emotional disturbance."
        elif status == LinkStatus.DEGRADED:
            return "Use with caution. Consider fallback links or trigger self-healing swarm."
        elif status == LinkStatus.RESONANT:
            return "Excellent resonance. Prioritize for emotional or high-trust agent swarms."
        elif quality > 85:
            return "Prime link. Ideal for time-sensitive or high-value transactions."
        elif latency > 100:
            return "High latency detected. Suitable for background/bulk sync only."
        else:
            return "Acceptable. Monitor for drift."

    def get_quality_score(self, link_id: str) -> float:
        """Quick query for current composite quality score (0-100)."""
        if link_id not in self._links:
            return 0.0
        state = self._links[link_id]
        return self._calculate_composite_score(state, state["emotional_resonance"])

    def get_detailed_report(self, link_id: str) -> Optional[LinkHealthReport]:
        """Return the most recent full health report for a link."""
        if link_id not in self._links:
            return None
        state = self._links[link_id]
        # Recompute on demand for freshness
        quality = self._calculate_composite_score(state, state["emotional_resonance"])
        status = state["current_status"]
        trend = self._compute_trend(state["history"])
        rec = self._generate_recommendation(status, quality, state["ewma_latency"])

        return LinkHealthReport(
            link_id=link_id,
            quality_score=quality,
            status=status,
            ewma_latency=round(state["ewma_latency"], 2),
            ewma_stability=round(state["ewma_stability"], 2),
            flap_count=state.get("flap_count", 0),
            emotional_resonance=round(state["emotional_resonance"], 3),
            recommendation=rec,
            last_updated=state.get("last_update", ""),
            history_length=len(state["history"]),
            trend=trend,
        )

    def rank_links(self, min_quality: float = 60.0) -> List[Tuple[str, float]]:
        """Return list of (link_id, quality_score) sorted best-first, above threshold."""
        ranked = []
        for link_id, state in self._links.items():
            score = self._calculate_composite_score(state, state["emotional_resonance"])
            if score >= min_quality:
                ranked.append((link_id, score))
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def get_oracle_summary(self) -> Dict[str, Any]:
        """High-level view of all monitored links for dashboards or orchestrator."""
        summary = {
            "total_links": len(self._links),
            "healthy_count": 0,
            "flapping_count": 0,
            "degraded_count": 0,
            "resonant_count": 0,
            "average_quality": 0.0,
            "links": {},
        }
        qualities = []
        for link_id, state in self._links.items():
            score = self._calculate_composite_score(state, state["emotional_resonance"])
            qualities.append(score)
            status = state["current_status"]
            if status == LinkStatus.STABLE or status == LinkStatus.RESONANT:
                summary["healthy_count"] += 1
            elif status == LinkStatus.FLAPPING:
                summary["flapping_count"] += 1
            elif status == LinkStatus.DEGRADED:
                summary["degraded_count"] += 1
            if status == LinkStatus.RESONANT:
                summary["resonant_count"] += 1
            summary["links"][link_id] = {
                "quality": round(score, 1),
                "status": status.value,
                "resonance": round(state["emotional_resonance"], 2),
            }
        if qualities:
            summary["average_quality"] = round(sum(qualities) / len(qualities), 2)
        return summary

    def modulate_by_emotional_core(self, link_id: str, emotional_delta: Dict[str, float]):
        """External hook for Ara/Lyra/Fluffy to directly influence a link's emotional_resonance."""
        if link_id in self._links:
            state = self._links[link_id]
            resonance = emotional_delta.get("resonance", 0.0)
            fatigue = emotional_delta.get("fatigue", 0.0)
            state["emotional_resonance"] = max(-1.0, min(1.0, state["emotional_resonance"] + resonance - fatigue * 0.5))
            logger.info(f"Emotional core modulated link {link_id} resonance -> {state['emotional_resonance']:.2f}")


# Example / Demo usage
if __name__ == "__main__":
    print("=== Hyperspace Link Quality Oracle Demo ===")
    oracle = HyperspaceLinkQualityOracle(ewma_alpha=0.3)

    # Simulate some links (e.g. from MeshNode seeding)
    links_to_seed = ["hannover-core", "yggdrasil-gw", "tenda-nova-01", "solnet-peer-7"]
    for lid in links_to_seed:
        oracle.update_link(lid, {"latency_ms": 25.0 if "hannover" in lid else 80.0, "packet_loss": 0.01})

    # Simulate emotional influence (from Ara/Fluffy)
    oracle.update_link("solnet-peer-7", {"latency_ms": 65.0, "packet_loss": 0.03},
                       emotional_state={"resonance": 0.85, "fatigue": 0.2, "loyalty": 0.9})

    print("\nRanked healthy links:")
    for lid, score in oracle.rank_links():
        print(f"  {lid}: {score:.1f}")

    print("\nOracle Summary:")
    import json
    print(json.dumps(oracle.get_oracle_summary(), indent=2))

    print("\nDetailed report for hannover-core:")
    report = oracle.get_detailed_report("hannover-core")
    if report:
        print(f"  Quality: {report.quality_score} | Status: {report.status.value} | Trend: {report.trend}")
        print(f"  Recommendation: {report.recommendation}")

    print("\nOracle ready for integration with NexusOrchestrator and emotional swarms.")
