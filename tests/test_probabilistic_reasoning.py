"""Tests for Probabilistic Reasoning Engine (Milestone 4)."""

import unittest
from prototype.cognition import (
    ProbabilisticReasoningEngine,
    BayesianInferenceEngine,
    UncertaintyEstimator,
    ConfidencePropagator,
    Hypothesis,
)
from prototype.common import EventBus


class TestProbabilisticReasoning(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = EventBus()
        self.engine = ProbabilisticReasoningEngine(event_bus=self.bus)
        self.engine.load()

    def test_bayesian_update(self) -> None:
        bayes = BayesianInferenceEngine()
        hypo = Hypothesis(name="High-confidence path", prior_probability=0.5)
        post = bayes.update_posterior(hypo, likelihood=0.8, p_evidence=0.5)
        self.assertGreater(post, 0.5)
        self.assertEqual(len(hypo.evidence_collected), 1)

    def test_uncertainty_estimator(self) -> None:
        estimator = UncertaintyEstimator()
        metrics = estimator.estimate([0.8, 0.85, 0.78, 0.82])
        self.assertLess(metrics.epistemic_uncertainty, 0.2)
        self.assertGreater(metrics.confidence_score, 0.5)

    def test_confidence_propagator(self) -> None:
        propagator = ConfidencePropagator()
        step_conf = {"step_1": 0.9, "step_2": 0.8}
        deps = {"step_2": ["step_1"]}
        res = propagator.propagate(step_conf, deps)
        self.assertEqual(res["step_2"], 0.72)

    def test_probabilistic_reasoning_engine_integration(self) -> None:
        eval_res = self.engine.evaluate_reasoning_hypothesis(
            hypothesis_name="Optimal API Tool Choice",
            evidence_likelihoods=[0.85, 0.90, 0.88],
        )
        self.assertEqual(eval_res["hypothesis"], "Optimal API Tool Choice")
        self.assertGreater(eval_res["posterior"], 0.5)
        self.assertIn("propagated_confidence", eval_res)


if __name__ == "__main__":
    unittest.main()
