from __future__ import annotations

import unittest
from pathlib import Path

from scripts.build_hybrid_inventory import simulate_live_listings
from scripts.import_kaggle_used_vehicles import load_rows, normalize_rows


class KaggleImporterTests(unittest.TestCase):
    def test_normalizes_toronto_kaggle_rows_and_drops_zero_prices(self) -> None:
        fixture = Path(__file__).resolve().parent / "fixtures" / "kaggle_used_vehicles_sample.csv"
        vehicles = normalize_rows(load_rows(fixture), limit=10)

        self.assertEqual(len(vehicles), 2)
        camry = vehicles[0]
        self.assertEqual(camry["listing_source"], "kaggle_toronto_used_vehicles")
        self.assertEqual(camry["country"], "Canada")
        self.assertEqual(camry["province"], "ON")
        self.assertEqual(camry["city"], "Toronto")
        self.assertEqual(camry["price_cad"], 28900)
        self.assertEqual(camry["mileage_km"], 53052)
        self.assertEqual(camry["body_style"], "sedan")
        self.assertEqual(camry["fuel_type"], "Gas")
        self.assertIn("backup camera", camry["features"])

    def test_simulated_live_inventory_keeps_valid_prices(self) -> None:
        fixture = Path(__file__).resolve().parent / "fixtures" / "kaggle_used_vehicles_sample.csv"
        vehicles = normalize_rows(load_rows(fixture), limit=10)

        simulated = simulate_live_listings(vehicles, count=2, seed=7)

        self.assertEqual(len(simulated), 2)
        self.assertTrue(all(vehicle["price_cad"] >= 3000 for vehicle in simulated))
        self.assertTrue(all(vehicle["listing_source"] == "simulated_live" for vehicle in simulated))
        self.assertTrue(all(vehicle["id"].startswith("live-") for vehicle in simulated))


if __name__ == "__main__":
    unittest.main()
