# Demo Inventory Data

`vehicles.json` is a local synthetic demo inventory. It is designed to look like a realistic Canadian used-car dataset without scraping live marketplaces or storing personal information.

The dataset includes:

- Vehicle identity: year, make, model, trim, body style, origin, seats, drivetrain, transmission, fuel type.
- Listing details: demo dealer name, Canadian city, province, country, mileage in kilometres, price in CAD, source type, exterior color, days on market.
- Recommendation features: reliability, performance, practicality, luxury, winter suitability, ownership cost, fun, family fit.
- Market fields: estimated local market average, price delta, and tracked price history snapshots.
- Risk fields: accident history status, certified pre-owned status, and notable features.

The `listing_source` value is `synthetic_demo`. The `source_url` values use a `demo://` URL scheme on purpose, so the app does not pretend these are real dealership listings.

For a production version, replace this with licensed listing feeds, allowed dealer APIs, or user-provided CSV exports. Avoid scraping sites that prohibit automated collection in their terms.

## External Dataset Mode

`scripts/import_kaggle_used_vehicles.py` normalizes the Kaggle Toronto/Ontario used-vehicles dataset into `data/private/vehicles.kaggle.json`. `scripts/build_hybrid_inventory.py` combines that file with `data/private/manual_listings.csv` and simulated live variants into `data/private/vehicles.hybrid.json`.

The current preferred app inventory is:

```text
data/private/vehicles.hybrid.json
```

It combines:

- Kaggle Toronto used-vehicle records with real price, mileage, body style, engine, drivetrain, fuel economy, and vehicle specification fields.
- Manual curated seed rows for models that shoppers commonly ask for directly, such as Supra, M440i, TLX Type S, Civic Type R, and older BMW sport sedans.
- Simulated live rows derived from the clean inventory to mimic new listings, short days-on-market values, and price changes.

The API loads `vehicles.hybrid.json` first when present, then falls back to Kaggle, Rebrowser, and finally the synthetic demo inventory.

`scripts/import_rebrowser_autotrader.py` can normalize local CSV exports from the Rebrowser AutoTrader dataset into `data/private/vehicles.rebrowser.json`. The raw files should live under `data/raw/`, and the normalized private output should live under `data/private/`; both paths are ignored by Git.

`scripts/update_rebrowser_inventory.py` can also download the latest free sample Parquet files from the public GitHub repository, cache them under `data/raw/`, and write the normalized `data/private/vehicles.rebrowser.json` file in one step. Parquet import requires `pyarrow`.

Rebrowser's AutoTrader dataset is US-oriented, so imported rows are marked as `country: "United States"` and converted from USD/miles into CAD/kilometres for comparison. The primary demo inventory remains Canada-first.

When `data/private/vehicles.rebrowser.json` exists, the API automatically uses that imported real-listing inventory instead of `data/vehicles.json`. Set `AUTOMATCH_DATA_PATH` to force a specific file.

The importer does not store VINs, seller phone numbers, seller street addresses, or stock numbers in the AutoMatch inventory. It keeps only the vehicle and listing fields needed by the recommender, including make/model/trim, price, mileage, city/state, listing URL, engine, drivetrain, fuel type, CPO status, vehicle-history preview, and feature tags.

Use Rebrowser data only under its license and terms. The repository describes the free sample as research/non-commercial with attribution, while commercial use requires a paid license.
