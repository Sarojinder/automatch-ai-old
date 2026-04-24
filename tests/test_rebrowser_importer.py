from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.import_rebrowser_autotrader import normalize_rows


class RebrowserImporterTests(unittest.TestCase):
    def test_normalizes_rebrowser_row_without_sensitive_fields(self) -> None:
        rows = [
            {
                "listingId": "AT-123",
                "vin": "1FAKEVIN000000001",
                "stockNumber": "STOCK-9",
                "year": "2023",
                "makeName": "Lexus",
                "modelName": "IS 350",
                "trim": "F Sport AWD",
                "bodyStyle": "SEDAN",
                "listingType": "Certified",
                "mileage": "18000",
                "salePrice": "34500",
                "kbbFairPurchasePrice": "36000",
                "drivetrain": "All wheel drive",
                "transmissionGroup": "Automatic",
                "engine": "6-Cylinder",
                "engineCode": "6CLDR",
                "fuelTypeGroup": "Gas",
                "mpgCity": "19",
                "mpgHighway": "26",
                "hasLeatherSeats": "true",
                "daysOnMarket": "33",
                "isReducedPrice": "true",
                "sellerName": "Demo Lexus",
                "sellerPhone": "555-123-4567",
                "sellerAddress": "1 Demo Street",
                "sellerCity": "Buffalo",
                "sellerState": "NY",
                "sellerRating": "4.7",
                "listingUrl": "https://example.com/listing/AT-123",
                "vhrPreview": '["NO_ACCIDENTS_REPORTED"]',
                "options": '{"interior":["Heated seats"],"technology":["Backup camera"]}',
                "exteriorColor": "Atomic Silver",
            }
        ]

        vehicles = normalize_rows(rows, limit=10, states={"NY"}, usd_to_cad=1.35)

        self.assertEqual(len(vehicles), 1)
        vehicle = vehicles[0]
        self.assertEqual(vehicle["listing_source"], "rebrowser_autotrader")
        self.assertEqual(vehicle["listing_type"], "Certified")
        self.assertEqual(vehicle["country"], "United States")
        self.assertEqual(vehicle["province"], "NY")
        self.assertEqual(vehicle["city"], "Buffalo")
        self.assertEqual(vehicle["origin"], "Japanese")
        self.assertEqual(vehicle["price_cad"], 46600)
        self.assertEqual(vehicle["mileage_km"], 28968)
        self.assertEqual(vehicle["engine"], "6-Cylinder")
        self.assertEqual(vehicle["cylinders"], 6)
        self.assertTrue(vehicle["cpo"])
        self.assertNotIn("vin", vehicle)
        self.assertNotIn("sellerPhone", vehicle)
        self.assertNotIn("sellerAddress", vehicle)

    def test_importer_filters_by_state(self) -> None:
        rows = [
            {
                "listingId": "AT-1",
                "year": "2022",
                "makeName": "Toyota",
                "modelName": "RAV4",
                "trim": "XLE",
                "bodyStyle": "SUV",
                "mileage": "20000",
                "salePrice": "28000",
                "sellerState": "TX",
            }
        ]

        self.assertEqual(normalize_rows(rows, limit=10, states={"NY"}, usd_to_cad=1.35), [])


if __name__ == "__main__":
    unittest.main()
