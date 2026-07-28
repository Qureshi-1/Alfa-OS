"""Probabilistic Reasoning Engine — Milestone 4 implementation for ALFA COS v1.1.

Components:
- Bayesian Inference: BayesianInferenceEngine (updates hypothesis posterior based on evidence likelihood)
- Uncertainty Estimation: UncertaintyEstimator (quantifies epistemic vs aleatoric uncertainty)
- Confidence Propagation: ConfidencePropagator (propagates confidence scores through step dependencies)
- Probabilistic Reasoning: ProbabilisticReasoningEngine composition root
"""

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import uuid4

from prototype.common import Event, EventBus

import logging
logger = logging.getLogger("alfa.cognition.probabilistic")


@dataclass
class Hypothesis:
    hypothesis_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    prior_probability: float = 0.5
    posterior_probability: float = 0.5
    evidence_collected: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class UncertaintyMetrics:
    epistemic_uncertainty: float = 0.0  # Model ignorance (reducible with more data)
    aleatoric_uncertainty: float = 0.0  # Stochastic noise (inherent randomness)
    total_uncertainty: float = 0.0
    confidence_score: float = 1.0


class BayesianInferenceEngine:
    """Computes Bayesian update P(H|E) = (P(E|H) * P(H)) / P(E)."""

    def update_posterior(self, hypothesis: Hypothesis, likelihood: float, p_evidence: float = 0.5) -> float:
        prior = hypothesis.prior_probability
        # Safe Bayesian update
        p_ev = max(0.01, min(0.99, p_evidence))
        posterior = (likelihood * prior) / p_ev
        posterior = max(0.01, min(0.99, posterior))
        hypothesis.posterior_probability = round(posterior, 4)
        hypothesis.evidence_collected.append({
            "likelihood": likelihood,
            "p_evidence": p_ev,
            "posterior": hypothesis.posterior_probability,
            "timestamp": time.time(),
        })
        return hypothesis.posterior_probability


class UncertaintyEstimator:
    """Estimates Epistemic (model uncertainty) and Aleatoric (data noise) uncertainty."""

    def estimate(self, probabilities: List[float]) -> UncertaintyMetrics:
        if not probabilities:
            return UncertaintyMetrics(total_uncertainty=1.0, confidence_score=0.0)

        n = len(probabilities)
        mean_p = sum(probabilities) / n

        # Epistemic uncertainty = standard deviation of probabilities (0.0 to 0.5)
        variance = sum((p - mean_p) ** 2 for p in probabilities) / n
        epistemic = math.sqrt(variance)

        # Aleatoric uncertainty = distance of mean probability from certainty (1.0 or 0.0)
        aleatoric = 1.0 - (2.0 * abs(mean_p - 0.5))

        total = round(min(1.0, (0.5 * epistemic) + (0.5 * aleatoric)), 4)
        confidence = round(max(0.0, 1.0 - total), 4)

        return UncertaintyMetrics(
            epistemic_uncertainty=round(epistemic, 4),
            aleatoric_uncertainty=round(aleatoric, 4),
            total_uncertainty=total,
            confidence_score=confidence,
        )


class ConfidencePropagator:
    """Propagates confidence through direct acyclic step graphs."""

    def propagate(self, step_confidences: Dict[str, float], dependencies: Dict[str, List[str]]) -> Dict[str, float]:
        propagated: Dict[str, float] = {}
        for step_id, conf in step_confidences.items():
            deps = dependencies.get(step_id, [])
            if not deps:
                propagated[step_id] = conf
            else:
                dep_confs = [propagated.get(d, 0.5) for d in deps]
                min_dep = min(dep_confs)
                propagated[step_id] = round(conf * min_dep, 4)
        return propagated


class ProbabilisticReasoningEngine:
    """Composition Root for Milestone 4 Probabilistic Reasoning Engine."""

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus or EventBus()
        self.bayesian = BayesianInferenceEngine()
        self.uncertainty = UncertaintyEstimator()
        self.propagator = ConfidencePropagator()
        self._loaded = False

    def load(self) -> None:
        self._loaded = True
        logger.info("ProbabilisticReasoningEngine loaded")

    def is_loaded(self) -> bool:
        return self._loaded

    def evaluate_reasoning_hypothesis(
        self,
        hypothesis_name: str,
        evidence_likelihoods: List[float],
        dependencies: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        hypo = Hypothesis(name=hypothesis_name, prior_probability=0.5)
        
        for lk in evidence_likelihoods:
            self.bayesian.update_posterior(hypo, likelihood=lk, p_evidence=0.6)

        metrics = self.uncertainty.estimate(evidence_likelihoods)
        
        step_conf = {"step_1": hypo.posterior_probability, "step_2": metrics.confidence_score}
        deps = dependencies or {"step_2": ["step_1"]}
        propagated_conf = self.propagator.propagate(step_conf, deps)

        self._event_bus.publish(Event(
            event_type="ProbabilisticReasoningEvaluated",
            payload={
                "hypothesis": hypothesis_name,
                "posterior": hypo.posterior_probability,
                "confidence": metrics.confidence_score,
            },
            source="probabilistic_reasoning",
        ))

        return {
            "hypothesis": hypothesis_name,
            "prior": hypo.prior_probability,
            "posterior": hypo.posterior_probability,
            "uncertainty": metrics.__dict__,
            "propagated_confidence": propagated_conf,
        }

    def rank_hypotheses(self, hypotheses: List[Hypothesis]) -> List[Hypothesis]:
        """Rank a list of hypotheses by posterior probability."""
        return sorted(hypotheses, key=lambda h: h.posterior_probability, reverse=True)

