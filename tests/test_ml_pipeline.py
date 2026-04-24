from __future__ import annotations

import unittest

from app.data_loader import load_vehicles
from app.ml_features import FEATURE_NAMES, build_feature_vector
from app.ml_ranker import model_status
from app.preferences import parse_preferences
from app.service import run_recommendation
from scripts.train_match_model import build_training_set


class MLPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vehicles = load_vehicles()

    def test_feature_vector_matches_declared_feature_names(self) -> None:
        profile = parse_preferences("fast but easy to maintain under 50k")
        vector = build_feature_vector(self.vehicles[0], profile)

        self.assertEqual(len(vector), len(FEATURE_NAMES))
        self.assertTrue(all(isinstance(value, float) for value in vector))

    def test_training_set_has_multiple_query_vehicle_examples(self) -> None:
        features, labels = build_training_set(self.vehicles[:12])

        self.assertEqual(features.shape[1], len(FEATURE_NAMES))
        self.assertEqual(len(features), len(labels))
        self.assertGreater(len(labels), 100)
        self.assertGreaterEqual(labels.min(), 0)
        self.assertLessEqual(labels.max(), 100)

    def test_recommendation_response_includes_model_metadata(self) -> None:
        payload = run_recommendation("car with good speakers under 45k", limit=3)

        self.assertIn("model", payload)
        self.assertEqual(payload["model"]["feature_count"], len(FEATURE_NAMES))
        self.assertTrue(payload["recommendations"])

    def test_model_status_is_safe_before_or_after_training(self) -> None:
        status = model_status()

        self.assertIn("available", status)
        self.assertIn("feature_count", status)


if __name__ == "__main__":
    unittest.main()
