from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "vehicles.json"
REFERENCE_YEAR = 2026
RANDOM = random.Random(20260417)

LOCATIONS = [
    "Toronto",
    "Mississauga",
    "Markham",
    "Vaughan",
    "Brampton",
    "Scarborough",
    "Oakville",
    "Hamilton",
    "Ottawa",
    "Kitchener",
    "London",
    "Barrie",
]

PROVINCE_BY_CITY = {
    "Toronto": "ON",
    "Mississauga": "ON",
    "Markham": "ON",
    "Vaughan": "ON",
    "Brampton": "ON",
    "Scarborough": "ON",
    "Oakville": "ON",
    "Hamilton": "ON",
    "Ottawa": "ON",
    "Kitchener": "ON",
    "London": "ON",
    "Barrie": "ON",
}

DEALERS = [
    "Maple Leaf Auto Group",
    "GTA Performance Motors",
    "Northline Certified Autos",
    "Lakeshore Luxury Cars",
    "Summit Family Motors",
    "Ontario Hybrid Centre",
    "Queenston Auto Mall",
    "Urban Drive Select",
    "PrimeWay Motors",
    "TrueNorth Auto House",
]

COLORS = [
    "Alpine White",
    "Crystal Black",
    "Sonic Grey",
    "Deep Blue",
    "Atomic Silver",
    "Soul Red",
    "Magnetite Grey",
    "Pearl White",
    "Caviar",
    "Racing Blue",
]

COMMON_FEATURES = {
    "luxury": ["leather seats", "heated steering wheel", "premium audio", "adaptive cruise"],
    "performance": ["sport suspension", "paddle shifters", "performance brakes"],
    "family": ["blind spot monitoring", "rear camera", "apple carplay", "heated rear seats"],
    "winter": ["heated seats", "remote start", "winter tire package"],
    "ev": ["battery warranty", "fast charging", "heat pump"],
}


CATALOG: list[dict[str, Any]] = [
    {
        "make": "BMW",
        "model": "M440i",
        "trim": "xDrive Coupe",
        "body_style": "coupe",
        "origin": "German",
        "base_price": 44900,
        "years": [2023, 2022],
        "seats": 4,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 382,
        "fuel_type": "Gas",
        "l_per_100km": 9.4,
        "scores": [6.9, 9.4, 5.6, 8.8, 8.2, 5.2, 9.2, 4.8],
        "tags": ["fun", "luxury", "awd", "performance"],
        "notes": "Excellent powertrain and premium feel, but maintenance planning matters.",
    },
    {
        "make": "BMW",
        "model": "328i",
        "trim": "xDrive Sedan",
        "body_style": "sedan",
        "origin": "German",
        "base_price": 21900,
        "years": [2016, 2014, 2012],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 240,
        "fuel_type": "Gas",
        "l_per_100km": 8.9,
        "scores": [6.1, 7.4, 6.4, 7.2, 7.4, 4.7, 7.6, 6.0],
        "tags": ["german", "luxury", "awd", "used"],
        "notes": "A classic older BMW pick: fun and premium, but maintenance records matter.",
    },
    {
        "make": "BMW",
        "model": "330i",
        "trim": "xDrive Sedan",
        "body_style": "sedan",
        "origin": "German",
        "base_price": 28900,
        "years": [2019, 2018, 2017],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 248,
        "fuel_type": "Gas",
        "l_per_100km": 8.5,
        "scores": [6.5, 7.8, 6.7, 7.8, 7.8, 5.0, 7.8, 6.2],
        "tags": ["german", "luxury", "awd", "sport-sedan"],
        "notes": "Newer old-BMW sweet spot with better tech, still worth budgeting for repairs.",
    },
    {
        "make": "Acura",
        "model": "TLX",
        "trim": "Type S SH-AWD",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 43800,
        "years": [2022, 2023],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 355,
        "fuel_type": "Gas",
        "l_per_100km": 10.6,
        "scores": [8.2, 8.5, 7.2, 8.0, 8.6, 7.0, 8.0, 7.2],
        "tags": ["japanese", "reliable", "sport-sedan", "awd"],
        "notes": "Strong match for someone who wants performance with a more reliability-minded brand.",
    },
    {
        "make": "Lexus",
        "model": "IS 350",
        "trim": "F Sport AWD",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 44900,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 311,
        "fuel_type": "Gas",
        "l_per_100km": 10.8,
        "scores": [9.2, 7.8, 6.8, 8.5, 8.0, 7.8, 7.5, 6.7],
        "tags": ["japanese", "reliable", "luxury", "awd"],
        "notes": "Less explosive than the BMW, but very strong on reliability, comfort, and resale.",
    },
    {
        "make": "Toyota",
        "model": "Camry",
        "trim": "XSE V6",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 31900,
        "years": [2020, 2019, 2018],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 301,
        "fuel_type": "Gas",
        "l_per_100km": 9.5,
        "cylinders": 6,
        "scores": [8.7, 7.4, 7.8, 7.0, 6.6, 7.9, 7.4, 7.6],
        "tags": ["japanese", "v6", "reliable", "sedan"],
        "notes": "Reliable midsize sedan with V6 power, good comfort, and sane ownership costs.",
    },
    {
        "make": "Honda",
        "model": "Accord",
        "trim": "Touring V6",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 26900,
        "years": [2017, 2016, 2015],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 278,
        "fuel_type": "Gas",
        "l_per_100km": 9.3,
        "cylinders": 6,
        "scores": [8.5, 7.2, 7.6, 7.0, 6.4, 8.0, 7.2, 7.4],
        "tags": ["japanese", "v6", "reliable", "sedan"],
        "notes": "Older V6 sedan that balances reliability, comfort, and stronger passing power.",
    },
    {
        "make": "Lexus",
        "model": "ES 350",
        "trim": "Luxury",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 35900,
        "years": [2019, 2018, 2017],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 302,
        "fuel_type": "Gas",
        "l_per_100km": 9.5,
        "cylinders": 6,
        "scores": [9.1, 6.9, 7.9, 8.6, 6.5, 7.6, 6.6, 7.8],
        "tags": ["japanese", "v6", "luxury", "reliable"],
        "notes": "Comfort-first V6 luxury sedan with excellent reliability and premium audio potential.",
    },
    {
        "make": "Genesis",
        "model": "G70",
        "trim": "3.3T Sport AWD",
        "body_style": "sedan",
        "origin": "Korean",
        "base_price": 39900,
        "years": [2022, 2023],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 365,
        "fuel_type": "Gas",
        "l_per_100km": 11.0,
        "scores": [7.4, 8.8, 6.7, 8.2, 8.3, 7.1, 8.6, 6.6],
        "tags": ["value", "luxury", "awd", "performance"],
        "notes": "High feature count and performance for the money.",
    },
    {
        "make": "Audi",
        "model": "S5",
        "trim": "Sportback Technik",
        "body_style": "hatchback",
        "origin": "German",
        "base_price": 48500,
        "years": [2022, 2021],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 349,
        "fuel_type": "Gas",
        "l_per_100km": 9.9,
        "scores": [6.6, 8.7, 7.4, 8.9, 8.7, 5.0, 8.4, 6.9],
        "tags": ["luxury", "awd", "sportback", "performance"],
        "notes": "Practical liftback shape and great interior, but ownership costs can climb.",
    },
    {
        "make": "Mercedes-Benz",
        "model": "C43",
        "trim": "AMG 4MATIC",
        "body_style": "sedan",
        "origin": "German",
        "base_price": 46900,
        "years": [2022, 2021],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 385,
        "fuel_type": "Gas",
        "l_per_100km": 10.4,
        "scores": [6.3, 8.8, 6.7, 8.7, 8.0, 4.8, 8.5, 6.5],
        "tags": ["luxury", "performance", "awd"],
        "notes": "Fast and premium, but long-term repair costs should be budgeted.",
    },
    {
        "make": "Subaru",
        "model": "WRX",
        "trim": "Sport Manual",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 34900,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Manual",
        "horsepower": 271,
        "fuel_type": "Gas",
        "l_per_100km": 10.8,
        "scores": [7.6, 7.9, 7.3, 5.6, 9.1, 7.2, 8.7, 6.8],
        "tags": ["japanese", "manual", "awd", "fun"],
        "notes": "Great all-weather enthusiast pick, though it is not a luxury car.",
    },
    {
        "make": "Mazda",
        "model": "Mazda3",
        "trim": "Sport GT Turbo AWD",
        "body_style": "hatchback",
        "origin": "Japanese",
        "base_price": 33800,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 250,
        "fuel_type": "Gas",
        "l_per_100km": 8.7,
        "scores": [8.4, 7.3, 7.0, 7.2, 8.5, 8.0, 7.7, 6.5],
        "tags": ["japanese", "awd", "value", "daily"],
        "notes": "Premium-feeling cabin, strong turbo torque, and reasonable ownership costs.",
    },
    {
        "make": "Toyota",
        "model": "GR Corolla",
        "trim": "Core",
        "body_style": "hatchback",
        "origin": "Japanese",
        "base_price": 46800,
        "years": [2023, 2024],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Manual",
        "horsepower": 300,
        "fuel_type": "Gas",
        "l_per_100km": 9.8,
        "scores": [8.6, 8.9, 6.6, 5.2, 8.7, 7.6, 9.3, 6.2],
        "tags": ["japanese", "manual", "awd", "enthusiast"],
        "notes": "Very fun and reliability-minded, but small and less refined.",
    },
    {
        "make": "Honda",
        "model": "Civic Type R",
        "trim": "Manual",
        "body_style": "hatchback",
        "origin": "Japanese",
        "base_price": 47900,
        "years": [2022, 2023],
        "seats": 4,
        "drivetrain": "FWD",
        "transmission": "Manual",
        "horsepower": 306,
        "fuel_type": "Gas",
        "l_per_100km": 9.6,
        "scores": [8.5, 9.0, 6.8, 5.8, 5.9, 7.4, 9.5, 5.6],
        "tags": ["japanese", "manual", "enthusiast", "fun"],
        "notes": "One of the best driver cars here, but winter use is less ideal than AWD options.",
    },
    {
        "make": "Hyundai",
        "model": "Elantra N",
        "trim": "Manual",
        "body_style": "sedan",
        "origin": "Korean",
        "base_price": 32900,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Manual",
        "horsepower": 276,
        "fuel_type": "Gas",
        "l_per_100km": 9.5,
        "scores": [7.4, 8.4, 7.1, 5.8, 5.8, 8.0, 9.0, 6.6],
        "tags": ["manual", "fun", "value", "performance"],
        "notes": "Big fun-per-dollar option with a practical sedan body.",
    },
    {
        "make": "Volkswagen",
        "model": "Golf R",
        "trim": "DSG",
        "body_style": "hatchback",
        "origin": "German",
        "base_price": 45500,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 315,
        "fuel_type": "Gas",
        "l_per_100km": 8.9,
        "scores": [7.0, 8.8, 7.3, 7.1, 8.8, 6.0, 9.0, 6.6],
        "tags": ["awd", "hatchback", "fun", "performance"],
        "notes": "Compact, quick, and winter-ready, with more practicality than most sports cars.",
    },
    {
        "make": "Kia",
        "model": "Stinger",
        "trim": "GT Limited AWD",
        "body_style": "hatchback",
        "origin": "Korean",
        "base_price": 41900,
        "years": [2022, 2021],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 368,
        "fuel_type": "Gas",
        "l_per_100km": 11.1,
        "scores": [7.3, 8.6, 7.7, 8.0, 8.1, 6.8, 8.4, 7.0],
        "tags": ["awd", "value", "performance", "practical"],
        "notes": "A strong value grand tourer with hatchback practicality.",
    },
    {
        "make": "Toyota",
        "model": "RAV4",
        "trim": "Hybrid XLE AWD",
        "body_style": "suv",
        "origin": "Japanese",
        "base_price": 38900,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 219,
        "fuel_type": "Hybrid",
        "l_per_100km": 6.0,
        "scores": [9.1, 5.8, 9.0, 6.4, 8.4, 9.0, 5.4, 9.1],
        "tags": ["japanese", "hybrid", "family", "awd"],
        "notes": "Excellent family and cost-of-ownership pick, not the most exciting choice.",
    },
    {
        "make": "Honda",
        "model": "CR-V",
        "trim": "Hybrid Touring AWD",
        "body_style": "suv",
        "origin": "Japanese",
        "base_price": 42800,
        "years": [2023, 2024],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 204,
        "fuel_type": "Hybrid",
        "l_per_100km": 6.4,
        "scores": [8.8, 5.9, 9.2, 7.1, 8.2, 8.7, 5.3, 9.3],
        "tags": ["japanese", "hybrid", "family", "awd"],
        "notes": "A family-first recommendation with strong reliability and fuel economy.",
    },
    {
        "make": "Kia",
        "model": "Telluride",
        "trim": "SX AWD",
        "body_style": "suv",
        "origin": "Korean",
        "base_price": 44800,
        "years": [2022, 2021],
        "seats": 7,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 291,
        "fuel_type": "Gas",
        "l_per_100km": 11.3,
        "scores": [7.5, 6.5, 9.4, 8.0, 8.4, 6.9, 5.6, 9.6],
        "tags": ["family", "three-row", "awd", "luxury"],
        "notes": "Very strong family SUV choice with three rows and premium-feeling features.",
    },
    {
        "make": "Hyundai",
        "model": "Palisade",
        "trim": "Ultimate Calligraphy AWD",
        "body_style": "suv",
        "origin": "Korean",
        "base_price": 43900,
        "years": [2022, 2021],
        "seats": 7,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 291,
        "fuel_type": "Gas",
        "l_per_100km": 11.1,
        "scores": [7.4, 6.3, 9.5, 8.4, 8.3, 7.0, 5.4, 9.7],
        "tags": ["family", "three-row", "awd", "luxury"],
        "notes": "Three-row comfort and tech with a strong value story.",
    },
    {
        "make": "Mazda",
        "model": "CX-5",
        "trim": "Signature Turbo AWD",
        "body_style": "suv",
        "origin": "Japanese",
        "base_price": 35800,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 256,
        "fuel_type": "Gas",
        "l_per_100km": 9.8,
        "scores": [8.5, 7.0, 8.2, 7.8, 8.5, 7.8, 7.0, 8.1],
        "tags": ["japanese", "family", "awd", "value"],
        "notes": "A compact SUV that feels more premium and more fun than most rivals.",
    },
    {
        "make": "Subaru",
        "model": "Outback",
        "trim": "Premier XT AWD",
        "body_style": "wagon",
        "origin": "Japanese",
        "base_price": 38900,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 260,
        "fuel_type": "Gas",
        "l_per_100km": 9.1,
        "scores": [8.1, 6.8, 8.8, 7.5, 9.3, 7.4, 6.8, 8.7],
        "tags": ["japanese", "awd", "wagon", "family"],
        "notes": "Excellent winter and family usability with wagon-like cargo space.",
    },
    {
        "make": "Acura",
        "model": "RDX",
        "trim": "A-Spec SH-AWD",
        "body_style": "suv",
        "origin": "Japanese",
        "base_price": 41800,
        "years": [2022, 2021],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 272,
        "fuel_type": "Gas",
        "l_per_100km": 10.3,
        "scores": [8.0, 7.1, 8.3, 8.0, 8.4, 7.0, 7.0, 8.1],
        "tags": ["japanese", "luxury", "family", "awd"],
        "notes": "A sporty premium SUV with a reliability-minded brand image.",
    },
    {
        "make": "Lexus",
        "model": "NX 350h",
        "trim": "Premium AWD",
        "body_style": "suv",
        "origin": "Japanese",
        "base_price": 45900,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 240,
        "fuel_type": "Hybrid",
        "l_per_100km": 6.0,
        "scores": [9.3, 6.1, 8.4, 8.5, 8.4, 8.8, 5.8, 8.4],
        "tags": ["japanese", "hybrid", "luxury", "family"],
        "notes": "A premium hybrid SUV with excellent reliability and ownership cost scores.",
    },
    {
        "make": "Toyota",
        "model": "Highlander",
        "trim": "Hybrid XLE AWD",
        "body_style": "suv",
        "origin": "Japanese",
        "base_price": 46900,
        "years": [2022, 2021],
        "seats": 7,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 243,
        "fuel_type": "Hybrid",
        "l_per_100km": 6.7,
        "scores": [9.0, 5.7, 9.2, 7.0, 8.5, 8.7, 5.2, 9.4],
        "tags": ["japanese", "hybrid", "family", "three-row"],
        "notes": "A very rational family choice with three rows and hybrid efficiency.",
    },
    {
        "make": "Honda",
        "model": "Civic",
        "trim": "Touring Sedan",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 27800,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 180,
        "fuel_type": "Gas",
        "l_per_100km": 6.9,
        "scores": [8.8, 5.8, 7.8, 6.9, 5.8, 8.8, 6.2, 7.4],
        "tags": ["japanese", "daily", "reliable", "value"],
        "notes": "A safe daily-driver pick with strong economy and resale.",
    },
    {
        "make": "Toyota",
        "model": "Corolla",
        "trim": "Hybrid LE",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 25900,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 138,
        "fuel_type": "Hybrid",
        "l_per_100km": 4.5,
        "scores": [9.3, 4.8, 7.4, 5.6, 5.7, 9.4, 4.7, 7.2],
        "tags": ["japanese", "hybrid", "reliable", "value"],
        "notes": "Maximum practicality and low cost, but not a performance pick.",
    },
    {
        "make": "Toyota",
        "model": "Camry",
        "trim": "XSE Hybrid",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 34200,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 208,
        "fuel_type": "Hybrid",
        "l_per_100km": 5.1,
        "scores": [9.1, 5.8, 8.0, 7.2, 5.9, 9.0, 5.6, 8.0],
        "tags": ["japanese", "hybrid", "reliable", "daily"],
        "notes": "Comfortable, efficient, and durable midsize sedan.",
    },
    {
        "make": "Honda",
        "model": "Accord",
        "trim": "Hybrid Touring",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 36900,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 204,
        "fuel_type": "Hybrid",
        "l_per_100km": 5.3,
        "scores": [8.8, 6.0, 8.2, 7.6, 5.9, 8.8, 5.9, 8.2],
        "tags": ["japanese", "hybrid", "daily", "comfortable"],
        "notes": "A polished daily sedan with strong fuel economy and space.",
    },
    {
        "make": "Tesla",
        "model": "Model 3",
        "trim": "Long Range AWD",
        "body_style": "sedan",
        "origin": "American",
        "base_price": 39900,
        "years": [2022, 2021],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 425,
        "fuel_type": "EV",
        "l_per_100km": 0.0,
        "scores": [7.0, 8.7, 7.5, 7.4, 8.1, 8.3, 8.0, 7.2],
        "tags": ["ev", "awd", "performance", "low-running-cost"],
        "notes": "Quick and low running cost, but charging access should fit the buyer's lifestyle.",
    },
    {
        "make": "Hyundai",
        "model": "Ioniq 5",
        "trim": "Preferred Long Range AWD",
        "body_style": "suv",
        "origin": "Korean",
        "base_price": 42900,
        "years": [2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 320,
        "fuel_type": "EV",
        "l_per_100km": 0.0,
        "scores": [7.6, 7.8, 8.5, 7.8, 8.2, 8.4, 7.4, 8.5],
        "tags": ["ev", "family", "awd", "value"],
        "notes": "Spacious EV crossover with fast charging and strong family usability.",
    },
    {
        "make": "Ford",
        "model": "Mustang",
        "trim": "GT Premium",
        "body_style": "coupe",
        "origin": "American",
        "base_price": 43900,
        "years": [2022, 2021],
        "seats": 4,
        "drivetrain": "RWD",
        "transmission": "Manual",
        "horsepower": 450,
        "fuel_type": "Gas",
        "l_per_100km": 13.8,
        "scores": [7.1, 8.9, 4.6, 6.8, 4.5, 6.0, 9.2, 4.3],
        "tags": ["manual", "fun", "performance", "rwd"],
        "notes": "Big fun and sound, but winter and family practicality are weak.",
    },
    {
        "make": "Chevrolet",
        "model": "Camaro",
        "trim": "2SS",
        "body_style": "coupe",
        "origin": "American",
        "base_price": 42900,
        "years": [2022, 2021],
        "seats": 4,
        "drivetrain": "RWD",
        "transmission": "Manual",
        "horsepower": 455,
        "fuel_type": "Gas",
        "l_per_100km": 14.1,
        "scores": [6.9, 9.0, 4.2, 6.4, 4.0, 5.8, 9.0, 4.0],
        "tags": ["manual", "fun", "performance", "rwd"],
        "notes": "Huge performance for the money, but visibility and practicality are compromises.",
    },
    {
        "make": "Volvo",
        "model": "S60",
        "trim": "B5 R-Design AWD",
        "body_style": "sedan",
        "origin": "Swedish",
        "base_price": 36900,
        "years": [2022, 2021],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 247,
        "fuel_type": "Gas",
        "l_per_100km": 8.5,
        "scores": [7.1, 7.0, 7.2, 8.3, 8.1, 6.3, 6.8, 7.0],
        "tags": ["luxury", "safety", "awd", "value"],
        "notes": "A comfort and safety play with good pricing, but not as sporty as the German options.",
    },
    {
        "make": "Infiniti",
        "model": "Q50",
        "trim": "Red Sport 400 AWD",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 40900,
        "years": [2022, 2021],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 400,
        "fuel_type": "Gas",
        "l_per_100km": 11.2,
        "scores": [7.5, 8.9, 6.9, 7.4, 8.1, 6.6, 8.3, 6.8],
        "tags": ["japanese", "awd", "performance", "value"],
        "notes": "Huge power for the money, but interior tech feels older.",
    },
    {
        "make": "Toyota",
        "model": "Yaris",
        "trim": "LE Hatchback",
        "body_style": "hatchback",
        "origin": "Japanese",
        "base_price": 11900,
        "years": [2016, 2014, 2012],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 106,
        "fuel_type": "Gas",
        "l_per_100km": 6.8,
        "scores": [8.7, 3.9, 6.4, 3.8, 4.8, 9.1, 4.2, 5.8],
        "tags": ["japanese", "cheap", "reliable", "commuter"],
        "notes": "Cheap, simple transportation with strong reliability and low running costs.",
    },
    {
        "make": "Honda",
        "model": "Fit",
        "trim": "LX",
        "body_style": "hatchback",
        "origin": "Japanese",
        "base_price": 13900,
        "years": [2017, 2015, 2013],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 130,
        "fuel_type": "Gas",
        "l_per_100km": 7.0,
        "scores": [8.6, 4.8, 7.4, 4.4, 4.9, 8.8, 5.6, 6.6],
        "tags": ["japanese", "cheap", "reliable", "practical"],
        "notes": "A tiny car with surprisingly good space and low ownership costs.",
    },
    {
        "make": "Toyota",
        "model": "Prius",
        "trim": "Hybrid",
        "body_style": "hatchback",
        "origin": "Japanese",
        "base_price": 15900,
        "years": [2016, 2014, 2012],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 134,
        "fuel_type": "Hybrid",
        "l_per_100km": 4.7,
        "scores": [9.0, 4.2, 7.2, 4.6, 4.9, 9.4, 4.2, 6.8],
        "tags": ["japanese", "cheap", "hybrid", "fuel-efficient"],
        "notes": "Excellent fuel economy and reliability, but not a fun car.",
    },
    {
        "make": "Mazda",
        "model": "Mazda3",
        "trim": "GS Sedan",
        "body_style": "sedan",
        "origin": "Japanese",
        "base_price": 13900,
        "years": [2016, 2014, 2012],
        "seats": 5,
        "drivetrain": "FWD",
        "transmission": "Automatic",
        "horsepower": 155,
        "fuel_type": "Gas",
        "l_per_100km": 7.4,
        "scores": [8.2, 5.8, 7.0, 5.1, 5.1, 8.4, 6.2, 6.8],
        "tags": ["japanese", "cheap", "daily", "value"],
        "notes": "A good cheap daily with more driving feel than most economy cars.",
    },
    {
        "make": "Porsche",
        "model": "911",
        "trim": "Carrera 4S",
        "body_style": "coupe",
        "origin": "German",
        "base_price": 154900,
        "years": [2024, 2023, 2021],
        "seats": 4,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 443,
        "fuel_type": "Gas",
        "l_per_100km": 11.5,
        "scores": [7.6, 9.8, 4.8, 9.4, 7.5, 3.8, 9.8, 3.8],
        "tags": ["luxury", "performance", "awd", "expensive"],
        "notes": "A high-end sports car with huge performance and premium running costs.",
    },
    {
        "make": "Porsche",
        "model": "Cayenne",
        "trim": "S AWD",
        "body_style": "suv",
        "origin": "German",
        "base_price": 104900,
        "years": [2024, 2023, 2021],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 468,
        "fuel_type": "Gas",
        "l_per_100km": 12.8,
        "scores": [7.0, 9.1, 8.2, 9.2, 8.2, 3.9, 8.8, 8.0],
        "tags": ["luxury", "performance", "awd", "suv", "expensive"],
        "notes": "A premium performance SUV for shoppers prioritizing luxury and speed.",
    },
    {
        "make": "BMW",
        "model": "M3",
        "trim": "Competition xDrive",
        "body_style": "sedan",
        "origin": "German",
        "base_price": 96900,
        "years": [2024, 2023, 2022],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 503,
        "fuel_type": "Gas",
        "l_per_100km": 11.0,
        "scores": [6.8, 9.6, 6.8, 8.9, 8.0, 4.2, 9.5, 6.2],
        "tags": ["luxury", "performance", "awd", "fun", "expensive"],
        "notes": "A serious performance sedan with winter traction and expensive upkeep.",
    },
    {
        "make": "Mercedes-Benz",
        "model": "GLE 53",
        "trim": "AMG 4MATIC+",
        "body_style": "suv",
        "origin": "German",
        "base_price": 92900,
        "years": [2024, 2023, 2021],
        "seats": 5,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 429,
        "fuel_type": "Gas",
        "l_per_100km": 12.4,
        "scores": [6.5, 8.8, 8.6, 9.3, 8.4, 3.8, 8.1, 8.5],
        "tags": ["luxury", "performance", "awd", "suv", "expensive"],
        "notes": "A high-end family SUV with strong performance and premium maintenance costs.",
    },
    {
        "make": "Lexus",
        "model": "LX 600",
        "trim": "Ultra Luxury",
        "body_style": "suv",
        "origin": "Japanese",
        "base_price": 129900,
        "years": [2024, 2023, 2022],
        "seats": 7,
        "drivetrain": "AWD",
        "transmission": "Automatic",
        "horsepower": 409,
        "fuel_type": "Gas",
        "l_per_100km": 13.8,
        "scores": [8.8, 7.6, 8.8, 9.6, 8.8, 4.8, 7.0, 8.9],
        "tags": ["japanese", "luxury", "awd", "family", "expensive"],
        "notes": "A flagship luxury SUV with Japanese reliability but high fuel and purchase costs.",
    },
]


HERO_OVERRIDES = {
    ("BMW", "M440i", 2023): {
        "id": "bmw-m440i-2023",
        "price_cad": 44900,
        "location": "Toronto",
        "mileage_km": 39000,
        "dealer_name": "GTA Performance Motors",
        "market_average_cad": 46200,
        "price_history_cad": [46900, 45900, 44900],
        "days_on_market": 42,
        "accident_history": "none_reported",
        "cpo": True,
        "exterior_color": "Alpine White",
    },
    ("Acura", "TLX", 2022): {
        "id": "acura-tlx-type-s-2022",
        "price_cad": 43800,
        "location": "Mississauga",
        "mileage_km": 47000,
        "dealer_name": "Northline Certified Autos",
        "market_average_cad": 44900,
        "price_history_cad": [45200, 44500, 43800],
        "days_on_market": 38,
        "accident_history": "none_reported",
        "cpo": True,
        "exterior_color": "Crystal Black",
    },
    ("Lexus", "IS 350", 2023): {
        "id": "lexus-is350-2023",
        "price_cad": 44900,
        "location": "Markham",
        "mileage_km": 28000,
        "dealer_name": "Lakeshore Luxury Cars",
        "market_average_cad": 46100,
        "price_history_cad": [45900, 45500, 44900],
        "days_on_market": 27,
        "accident_history": "none_reported",
        "cpo": True,
        "exterior_color": "Atomic Silver",
    },
    ("Toyota", "Camry", 2020): {
        "id": "toyota-camry-xse-v6-2020",
        "price_cad": 28500,
        "location": "Toronto",
        "mileage_km": 58000,
        "dealer_name": "Queenston Auto Mall",
        "market_average_cad": 29900,
        "price_history_cad": [30400, 29400, 28500],
        "days_on_market": 44,
        "accident_history": "none_reported",
        "cpo": False,
        "exterior_color": "Magnetite Grey",
    },
    ("Lexus", "ES 350", 2019): {
        "id": "lexus-es350-luxury-2019",
        "price_cad": 29900,
        "location": "Markham",
        "mileage_km": 56000,
        "dealer_name": "Lakeshore Luxury Cars",
        "market_average_cad": 31700,
        "price_history_cad": [32200, 30900, 29900],
        "days_on_market": 51,
        "accident_history": "none_reported",
        "cpo": False,
        "exterior_color": "Alpine White",
    },
    ("Toyota", "RAV4", 2023): {
        "id": "toyota-rav4-hybrid-2023",
        "price_cad": 38900,
        "location": "Toronto",
        "mileage_km": 26000,
        "dealer_name": "Ontario Hybrid Centre",
        "market_average_cad": 39700,
        "price_history_cad": [39750, 39300, 38900],
        "days_on_market": 31,
        "accident_history": "none_reported",
        "cpo": True,
        "exterior_color": "Pearl White",
    },
}


def main() -> None:
    vehicles = build_inventory()
    OUTPUT_PATH.write_text(json.dumps(vehicles, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(vehicles)} demo vehicles to {OUTPUT_PATH}")


def build_inventory() -> list[dict[str, Any]]:
    vehicles: list[dict[str, Any]] = []

    for model_index, spec in enumerate(CATALOG):
        for year_index, year in enumerate(listing_years(spec)):
            location = LOCATIONS[(model_index * 2 + year_index * 3) % len(LOCATIONS)]
            province = PROVINCE_BY_CITY[location]
            dealer = DEALERS[(model_index + year_index) % len(DEALERS)]
            price = estimate_price(spec["base_price"], year, year_index)
            mileage = estimate_mileage(year, model_index, year_index)
            market_average = estimate_market_average(price, spec, year_index)
            price_history = build_price_history(price, market_average, model_index, year_index)
            accident_history = choose_accident_history(spec, model_index, year_index)
            cpo = year >= 2021 and accident_history == "none_reported" and (model_index + year_index) % 3 != 0

            vehicle = {
                "id": make_id(spec, year, location, year_index),
                "make": spec["make"],
                "model": spec["model"],
                "trim": spec["trim"],
                "year": year,
                "body_style": spec["body_style"],
                "origin": spec["origin"],
                "price_cad": price,
                "location": f"{location}, {province}",
                "country": "Canada",
                "province": province,
                "city": location,
                "mileage_km": mileage,
                "seats": spec["seats"],
                "drivetrain": spec["drivetrain"],
                "transmission": spec["transmission"],
                "horsepower": spec["horsepower"],
                "fuel_type": spec["fuel_type"],
                "engine": engine_description(spec),
                "cylinders": estimate_cylinders(spec),
                "l_per_100km": spec["l_per_100km"],
                "listing_type": "Used",
                "reliability": spec["scores"][0],
                "performance": spec["scores"][1],
                "practicality": spec["scores"][2],
                "luxury": spec["scores"][3],
                "winter": spec["scores"][4],
                "ownership_cost": spec["scores"][5],
                "fun": spec["scores"][6],
                "family": spec["scores"][7],
                "tags": spec["tags"],
                "notes": spec["notes"],
                "dealer_name": dealer,
                "listing_source": "synthetic_demo",
                "source_url": "",
                "market_average_cad": market_average,
                "days_on_market": 18 + ((model_index * 11 + year_index * 17) % 126),
                "price_history_cad": price_history,
                "accident_history": accident_history,
                "cpo": cpo,
                "features": build_features(spec),
                "exterior_color": COLORS[(model_index + year_index * 2) % len(COLORS)],
            }

            override = HERO_OVERRIDES.get((spec["make"], spec["model"], year))
            if override:
                vehicle.update(override)
                override_city = vehicle["location"].split(",")[0].strip()
                vehicle["city"] = override_city
                vehicle["province"] = PROVINCE_BY_CITY.get(override_city, vehicle.get("province", "ON"))
                vehicle["location"] = f"{vehicle['city']}, {vehicle['province']}"
                vehicle["country"] = "Canada"

            vehicle["listing_type"] = "Certified" if vehicle["cpo"] else "Used"
            vehicle["source_url"] = f"demo://inventory/{vehicle['id']}"
            vehicles.append(vehicle)

    return vehicles


def listing_years(spec: dict[str, Any]) -> list[int]:
    years = list(spec["years"])
    oldest = min(years)
    if oldest > 2020:
        years.append(oldest - 1)
    if oldest > 2019:
        years.append(2019)
    else:
        years.append(max(oldest - 2, 2010))
    return list(dict.fromkeys(years))


def estimate_price(base_price: int, year: int, year_index: int) -> int:
    age = max(REFERENCE_YEAR - year, 0)
    depreciation = age * 1850
    variation = (year_index * 700) - 350
    price = base_price - depreciation + variation
    return max(4900, round_to_nearest_100(price))


def estimate_mileage(year: int, model_index: int, year_index: int) -> int:
    age = max(REFERENCE_YEAR - year, 1)
    base = age * 13500
    variation = (model_index * 2300 + year_index * 4700) % 18000
    return round_to_nearest_1000(base + variation + 8000)


def estimate_cylinders(spec: dict[str, Any]) -> int | None:
    if "cylinders" in spec:
        return int(spec["cylinders"])
    if spec["fuel_type"] == "EV":
        return 0

    name = f"{spec['make']} {spec['model']} {spec['trim']}".lower()
    if any(token in name for token in ("lx 600", "cayenne s")):
        return 8
    if any(
        token in name
        for token in (
            "m440i",
            "m3",
            "g70",
            "s5",
            "c43",
            "tlx",
            "is 350",
            "q50",
            "supra",
            "911",
            "gle 53",
        )
    ):
        return 6
    return 4


def engine_description(spec: dict[str, Any]) -> str:
    cylinders = estimate_cylinders(spec)
    if cylinders == 0:
        return "Electric motor"
    if cylinders is None:
        return "Gas engine"

    name = f"{spec['make']} {spec['model']} {spec['trim']}".lower()
    forced_induction = "Turbocharged " if "turbo" in name or any(token in name for token in ("m440i", "m3", "g70", "s5", "c43", "q50", "gle 53", "cayenne")) else ""
    return f"{forced_induction}{cylinders}-cylinder {spec['fuel_type']} engine"


def estimate_market_average(price: int, spec: dict[str, Any], year_index: int) -> int:
    score_bias = int((spec["scores"][0] + spec["scores"][1] + spec["scores"][5] - 21) * 350)
    listing_delta = [1800, 900, -1200, 2400][year_index % 4]
    return round_to_nearest_100(price + listing_delta + score_bias)


def build_price_history(price: int, market_average: int, model_index: int, year_index: int) -> list[int]:
    first_premium = 900 + ((model_index * 313 + year_index * 211) % 2600)
    second_premium = max(300, first_premium // 2)
    if market_average < price:
        first_premium = max(400, first_premium - 700)
    return [
        round_to_nearest_100(price + first_premium),
        round_to_nearest_100(price + second_premium),
        price,
    ]


def choose_accident_history(spec: dict[str, Any], model_index: int, year_index: int) -> str:
    if spec["origin"] == "Japanese" and spec["scores"][0] >= 8.4:
        options = ["none_reported", "none_reported", "none_reported", "unknown"]
    else:
        options = ["none_reported", "none_reported", "minor_reported", "unknown"]
    return options[(model_index + year_index) % len(options)]


def build_features(spec: dict[str, Any]) -> list[str]:
    features = set(["apple carplay", "backup camera"])
    performance = spec["scores"][1]
    luxury = spec["scores"][3]
    fun = spec["scores"][6]
    family = spec["scores"][7]

    if spec["drivetrain"] == "AWD":
        features.update(COMMON_FEATURES["winter"])
    if luxury >= 7.4:
        features.update(COMMON_FEATURES["luxury"])
    if luxury >= 8.0:
        features.add("sunroof")
    if luxury >= 8.5:
        features.add("ventilated seats")
    if performance >= 8.0 or fun >= 8.5:
        features.update(COMMON_FEATURES["performance"])
    if "turbocharged" in engine_description(spec).lower():
        features.add("turbocharged")
    if family >= 8.0:
        features.update(COMMON_FEATURES["family"])
    if spec["fuel_type"] == "EV":
        features.update(COMMON_FEATURES["ev"])
    return sorted(features)


def make_id(spec: dict[str, Any], year: int, location: str, year_index: int) -> str:
    base = f"{year}-{spec['make']}-{spec['model']}-{spec['trim']}-{location}-{year_index}"
    return slugify(base)


def slugify(value: str) -> str:
    value = value.lower().replace("+", "plus")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return re.sub(r"-+", "-", value)


def round_to_nearest_100(value: int | float) -> int:
    return int(round(value / 100) * 100)


def round_to_nearest_1000(value: int | float) -> int:
    return int(round(value / 1000) * 1000)


if __name__ == "__main__":
    main()
