from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import unittest

from app.data_loader import load_vehicles
from app.finance import monthly_payment
from app.preferences import parse_preferences
from app.recommender import recommend_vehicles


class RecommenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        synthetic_path = Path(__file__).resolve().parents[1] / "data" / "vehicles.json"
        cls.vehicles = load_vehicles(synthetic_path)

    def test_fun_luxury_query_recommends_performance_cars(self) -> None:
        profile = parse_preferences("around 45k fun luxury 2022-2023 near Toronto")
        results = recommend_vehicles(self.vehicles, profile, limit=3)
        result_ids = {result.vehicle.id for result in results}

        self.assertTrue({"bmw-m440i-2023", "genesis-g70-33t-2022"} & result_ids)
        self.assertGreater(results[0].score, 90)

    def test_japanese_reliability_query_filters_to_japanese_origin(self) -> None:
        profile = parse_preferences("around 45k japanese reliability luxury fun daily driver with awd")
        results = recommend_vehicles(self.vehicles, profile, limit=5)

        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.origin == "Japanese" for result in results))
        self.assertIn(results[0].vehicle.make, {"Acura", "Lexus"})
        self.assertGreaterEqual(results[0].vehicle.reliability, 8.0)

    def test_expanded_inventory_has_market_fields(self) -> None:
        self.assertGreaterEqual(len(self.vehicles), 90)
        self.assertTrue(any(vehicle.market_average_cad for vehicle in self.vehicles))
        self.assertTrue(any(vehicle.price_history_cad for vehicle in self.vehicles))
        self.assertTrue(all(vehicle.country == "Canada" for vehicle in self.vehicles))
        self.assertTrue(all(vehicle.province == "ON" for vehicle in self.vehicles))

    def test_inventory_has_broad_price_range(self) -> None:
        prices = [vehicle.price_cad for vehicle in self.vehicles]

        self.assertLessEqual(min(prices), 6000)
        self.assertGreaterEqual(max(prices), 120000)
        self.assertTrue(any(vehicle.price_cad < 10000 for vehicle in self.vehicles))
        self.assertTrue(any(vehicle.price_cad > 100000 for vehicle in self.vehicles))

    def test_family_query_prioritizes_practicality(self) -> None:
        profile = parse_preferences("family suv under 45k reliable good in winter near Toronto")
        results = recommend_vehicles(self.vehicles, profile, limit=3)

        self.assertTrue(results)
        self.assertEqual(results[0].vehicle.body_style, "suv")
        self.assertGreaterEqual(results[0].vehicle.family, 8.5)
        self.assertIsNone(profile.max_mileage_km)

    def test_budget_k_is_not_confused_with_mileage(self) -> None:
        budget_profile = parse_preferences("under 45k reliable family suv")
        mileage_profile = parse_preferences("under 80k km reliable family suv")
        combined_profile = parse_preferences("under 80k km japanese reliable awd around 45k")

        self.assertEqual(budget_profile.budget_max, 45000)
        self.assertIsNone(budget_profile.max_mileage_km)
        self.assertIsNone(mileage_profile.budget_max)
        self.assertEqual(mileage_profile.max_mileage_km, 80000)
        self.assertEqual(combined_profile.budget_max, 45000)
        self.assertEqual(combined_profile.max_mileage_km, 80000)

    def test_2010s_used_query_parses_year_and_listing_type(self) -> None:
        profile = parse_preferences("used reliable suv from the 2010s under 30k")

        self.assertEqual(profile.year_min, 2010)
        self.assertEqual(profile.year_max, 2019)
        self.assertIn("Used", profile.listing_types)

    def test_hybrid_fuel_economy_query_filters_to_hybrids(self) -> None:
        profile = parse_preferences("hybrid suv with great fuel economy under 45k")
        results = recommend_vehicles(self.vehicles, profile, limit=5)

        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.fuel_type == "Hybrid" for result in results))
        self.assertIn("fuel_economy", profile.priorities)

    def test_cpo_query_prefers_certified_inventory(self) -> None:
        profile = parse_preferences("certified pre-owned reliable awd suv under 45k")
        results = recommend_vehicles(self.vehicles, profile, limit=5)

        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.listing_type == "Certified" for result in results))

    def test_dirt_cheap_query_returns_low_price_inventory(self) -> None:
        profile = parse_preferences("dirt cheap reliable car in Ontario")
        results = recommend_vehicles(self.vehicles, profile, limit=5)

        self.assertEqual(profile.budget_max, 10000)
        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.price_cad <= 11200 for result in results))

    def test_high_end_query_returns_expensive_inventory(self) -> None:
        profile = parse_preferences("expensive high-end luxury suv near Toronto")
        results = recommend_vehicles(self.vehicles, profile, limit=5)

        self.assertEqual(profile.budget_min, 60000)
        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.price_cad >= 60000 for result in results))

    def test_no_budget_does_not_trigger_budget_car_intent(self) -> None:
        profile = parse_preferences("no budget high-end performance suv")
        results = recommend_vehicles(self.vehicles, profile, limit=5)

        self.assertIsNone(profile.budget_max)
        self.assertEqual(profile.budget_min, 60000)
        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.price_cad >= 60000 for result in results))

    def test_six_figure_query_returns_six_figure_inventory(self) -> None:
        profile = parse_preferences("six figure performance car awd")
        results = recommend_vehicles(self.vehicles, profile, limit=5)

        self.assertEqual(profile.budget_min, 100000)
        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.price_cad >= 100000 for result in results))

    def test_ontario_location_query_is_understood(self) -> None:
        profile = parse_preferences("reliable awd suv under 45k in Ontario")
        results = recommend_vehicles(self.vehicles, profile, limit=3)

        self.assertEqual(profile.location, "ON")
        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.province == "ON" for result in results))

    def test_v6_sedan_mileage_query_uses_powertrain_and_mileage(self) -> None:
        profile = parse_preferences("v6 cars 30k 60k km ontario any year sedan")
        results = recommend_vehicles(self.vehicles, profile, limit=3)

        self.assertEqual(profile.budget_max, 30000)
        self.assertEqual(profile.max_mileage_km, 60000)
        self.assertEqual(profile.location, "ON")
        self.assertIn(6, profile.engine_cylinders)
        self.assertIn("sedan", profile.body_styles)
        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.cylinders == 6 for result in results))
        self.assertTrue(all(result.vehicle.body_style == "sedan" for result in results))
        self.assertTrue(all(result.vehicle.mileage_km <= 60000 for result in results))

    def test_model_name_query_filters_to_requested_model(self) -> None:
        base = self.vehicles[0]
        accord = replace(
            base,
            id="honda-accord-test",
            make="Honda",
            model="Accord",
            trim="Touring",
            body_style="sedan",
            origin="Japanese",
        )
        supra = replace(
            base,
            id="toyota-supra-test",
            make="Toyota",
            model="Supra",
            trim="3.0 Premium",
            body_style="coupe",
            origin="Japanese",
            performance=9.0,
            fun=9.0,
        )

        profile = parse_preferences("Supra")
        results = recommend_vehicles([accord, supra], profile, limit=3)

        self.assertTrue(results)
        self.assertTrue(all(result.vehicle.model == "Supra" for result in results))
        self.assertIn("requested Toyota Supra", results[0].reasons[0])

    def test_american_muscle_archetype_avoids_large_suvs(self) -> None:
        base = self.vehicles[0]
        escalade = replace(
            base,
            id="cadillac-escalade-test",
            make="Cadillac",
            model="Escalade",
            trim="Base",
            body_style="suv",
            origin="American",
            cylinders=8,
            performance=8.6,
            fun=4.0,
        )
        mustang = replace(
            base,
            id="ford-mustang-test",
            make="Ford",
            model="Mustang",
            trim="GT",
            body_style="coupe",
            origin="American",
            cylinders=8,
            drivetrain="RWD",
            performance=9.0,
            fun=9.0,
            tags=("performance", "muscle"),
        )

        profile = parse_preferences("american muscle")
        results = recommend_vehicles([escalade, mustang], profile, limit=3)

        self.assertIn("american_muscle", profile.archetypes)
        self.assertEqual(results[0].vehicle.model, "Mustang")
        self.assertTrue(all(result.vehicle.body_style != "suv" for result in results))

    def test_tuner_archetype_prefers_compact_enthusiast_cars(self) -> None:
        base = self.vehicles[0]
        civic = replace(
            base,
            id="honda-civic-si-test",
            make="Honda",
            model="Civic",
            trim="Si",
            body_style="sedan",
            origin="Japanese",
            price_cad=25000,
            transmission="Manual",
            performance=7.8,
            fun=8.8,
            ownership_cost=8.2,
            tags=("japanese", "tuner", "manual"),
            features=("sport suspension",),
        )
        rx = replace(
            base,
            id="lexus-rx-test",
            make="Lexus",
            model="RX",
            trim="350",
            body_style="suv",
            origin="Japanese",
            price_cad=25000,
            performance=6.5,
            fun=4.5,
            ownership_cost=7.0,
        )

        profile = parse_preferences("tuner car under 30k")
        results = recommend_vehicles([rx, civic], profile, limit=3)

        self.assertIn("tuner", profile.archetypes)
        self.assertEqual(results[0].vehicle.model, "Civic")
        self.assertTrue(all(result.vehicle.body_style != "suv" for result in results))

    def test_unknown_specific_model_query_does_not_return_random_cars(self) -> None:
        profile = parse_preferences("Supra")
        results = recommend_vehicles(self.vehicles, profile, limit=3)

        self.assertEqual(results, [])

    def test_finance_payment_is_positive(self) -> None:
        payment = monthly_payment(40000, annual_rate=7.99, months=60)

        self.assertGreater(payment, 0)
        self.assertLess(payment, 1000)


if __name__ == "__main__":
    unittest.main()
