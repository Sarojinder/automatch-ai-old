# AutoMatch AI

A Canada-focused vehicle recommendation platform built with Python, FastAPI, React, and scikit-learn, where the user describes the kind of car they want in natural language and receives ranked recommendations based on budget, mileage, location, features, ownership cost, driving character, and car-shopping intent.

The main experience is a natural-language search flow. The user enters prompts like “american muscle under 45k,” “tuner car under 30k,” or “family SUV with good speakers near Toronto,” and the system parses the request, filters a hybrid inventory, scores the best matches, explains why each vehicle fits, flags tradeoffs, and estimates financing.

## Features

- natural-language vehicle search
- budget parsing in CAD
- mileage parsing in kilometres
- location parsing for Canadian cities and provinces
- year range parsing
- body style filtering
- fuel type filtering
- drivetrain filtering
- engine cylinder filtering
- feature requirement parsing
- accident history filtering
- new, used, and certified inventory filtering
- car-culture archetype detection
- American muscle intent handling
- tuner car intent handling
- JDM intent handling
- German performance intent handling
- family hauler intent handling
- winter daily intent handling
- luxury cruiser intent handling
- cheap reliable car intent handling
- hard-filter recommendation pipeline
- weighted rule-based scoring
- machine-learning match ranking
- explanation-based recommendations
- caution flags for weak tradeoffs
- financing estimates with monthly payment, total paid, and interest
- hybrid inventory built from Kaggle data, curated seed rows, and simulated live listings
- representative vehicle image lookup with Wikimedia Commons fallback
- local dataset loading with fallback order
- health endpoint and recommendation API
- React frontend with result cards and parsed-preference summary
- automated tests for parsing, archetypes, recommendation behavior, and ML pipeline

## Tools

- Python
- FastAPI
- scikit-learn
- React
- Vite
- JavaScript
- Kaggle dataset tooling

## Files

- `app/api.py` - FastAPI routes and frontend/static serving
- `app/service.py` - recommendation service entry point and shared loaded inventory
- `app/data_loader.py` - dataset loading and fallback order
- `app/models.py` - vehicle, preference, finance, and recommendation data models
- `app/preferences.py` - natural-language parsing for budgets, mileage, filters, and features
- `app/archetypes.py` - car-culture intent mapping, aliases, and archetype scoring
- `app/recommender.py` - hard filters, rule-based scoring, ML score blending, and explanations
- `app/ml_features.py` - ML feature engineering
- `app/ml_ranker.py` - saved model loading and prediction
- `app/finance.py` - monthly payment and financing calculations
- `app/assistant.py` - recommendation summaries and follow-up questions
- `scripts/import_kaggle_used_vehicles.py` - Kaggle dataset normalization into app schema
- `scripts/build_hybrid_inventory.py` - hybrid inventory builder for Kaggle, curated, and simulated listings
- `scripts/train_match_model.py` - ML training pipeline and model card generation
- `tests/test_recommender.py` - recommendation and archetype behavior tests
- `web/src/main.jsx` - frontend search flow and recommendation UI
- `web/src/styles.css` - frontend styling
- `README.md` - project overview

## What I learned

- designing a recommendation system around structured constraints instead of chatbot-only output
- parsing messy car-shopping language into usable filters and priorities
- modeling vehicle data with pricing, mileage, market, and ownership fields
- handling car-culture search intent like muscle, tuner, JDM, family, and winter daily
- combining rule-based ranking with machine-learning prediction
- generating synthetic labels for supervised ranking when real labels do not exist
- engineering ML features from structured vehicle and preference data
- training and evaluating a gradient-boosting ranking model
- building a FastAPI backend and React frontend for the same product
- designing explanation-first recommendations with reasons and cautions
- estimating financing and monthly payment tradeoffs
- cleaning and normalizing messy vehicle listing datasets
- structuring a hybrid local dataset for a portfolio-quality prototype
- testing parsing, ranking, and edge cases like typo handling and archetype mismatches
