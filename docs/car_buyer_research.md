# AutoMatch AI Car-Buyer Research Notes

These notes turn broad car-shopping behavior into product requirements for the recommender.

## Core Buyer Signals

AutoMatch should understand both hard constraints and subjective intent.

- Price and financing: max budget, min budget, monthly payment, down payment, loan term, and total cost.
- Used-car risk: mileage, model year, accident history, certified pre-owned status, days on market, price drops, and market delta.
- Reliability and ownership: predicted repair risk, maintenance cost, fuel economy, insurance sensitivity, resale value, and known brand/model reputation.
- Body and use case: sedan, coupe, hatchback, SUV, wagon, truck, van, convertible, roadster, 2-door/4-door expectations, cargo needs, and seating.
- Canadian practicality: AWD, winter tires, heated seats, heated steering wheel, remote start, ground clearance, and location/province.
- Driving experience: horsepower, cylinders, manual/automatic, RWD/AWD/FWD, turbo, sport suspension, and enthusiast model lineage.
- Comfort and tech: premium audio, leather, ventilated seats, adaptive cruise, blind spot monitoring, backup camera, Apple CarPlay, and quiet ride.
- Car-culture language: American muscle, JDM, tuner car, sleeper, winter beater, family hauler, luxury cruiser, German performance, cheap reliable.

## Source-Informed Product Choices

- Consumer Reports frames used-car shopping around budget, safety, reliability, and whether to buy used, certified pre-owned, or new.
- J.D. Power ratings explicitly consider quality/reliability, driving experience, resale value, and dealership experience, which maps well to AutoMatch scoring.
- Wikimedia Commons guidance prefers free, clearly identified, representative vehicle images rather than fair-use promotional photos. The UI should therefore use Wikimedia images when available and fall back to local body-style artwork.
- Kaggle structured used-vehicle data gives price, mileage, body, engine, drivetrain, fuel, and model coverage, but it does not understand car-culture intent. That gap is covered with archetype rules and curated seed rows.

## Archetype Layer

The recommender now treats these as first-class parsed intents:

- American muscle: Mustang, Camaro, Challenger, Charger, Corvette; coupe/convertible/sedan; V8/RWD/performance; avoid SUVs, vans, trucks, hybrids.
- Tuner car: Civic, Type R, WRX/STI, BRZ/GR86, GTI/Golf R, Miata/MX-5, 350Z/370Z, Supra, Integra, BMW 335i/340i/M3; compact, manual, turbo, sport suspension.
- JDM / Japanese enthusiast: Japanese origin plus sporty Toyota, Honda, Acura, Lexus, Mazda, Nissan, Subaru models.
- German performance: BMW, Audi, Mercedes-Benz, Porsche, Volkswagen performance trims with turbo, sport suspension, luxury/performance balance.
- Family hauler: SUV, van, wagon, sedan; 5+ seats; safety tech, cargo space, winter confidence, reliability.
- Winter daily: AWD preference when requested, winter features, reliability, heated equipment, ownership cost.
- Luxury cruiser: premium brands, quiet/comfortable ride, premium audio, leather, ventilated seats, adaptive cruise.
- Cheap reliable: lower budget, simple ownership, Japanese/Korean preference, high reliability and low cost.
- Off-road / trail: SUV/truck, ground-clearance-friendly models, camping/trail language.

## What Not To Do

- Do not treat "American" and "American muscle" as the same thing.
- Do not treat every powerful vehicle as sporty if the body style violates the prompt.
- Do not return SUVs for muscle/tuner searches unless the user explicitly asks for an SUV.
- Do not require a paid API or scraping to make the prototype convincing.
- Do not use random web images without a reusable license path.

## Sources

- Consumer Reports used-car buying guide: https://www.consumerreports.org/cars/used-cars/buying-guide/
- J.D. Power ratings methodology: https://www.jdpower.com/ratings-methodology
- Wikimedia Commons automobile image guidance: https://commons.wikimedia.org/wiki/Commons:WikiProject_Automobiles
- Kaggle used vehicles for sale dataset: https://www.kaggle.com/datasets/farhanhossein/used-vehicles-for-sale
