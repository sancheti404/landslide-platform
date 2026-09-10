# Landslide ML Module

This module contains the Machine Learning components of the Landslide Intelligence Platform.

## Objective

Build a landslide susceptibility prediction model for Uttarakhand, India.

## Initial Model

XGBoost binary classification.

Target:

- 1 = Landslide occurrence
- 0 = Non-landslide sample

## Planned Features

- Latitude
- Longitude
- Elevation
- Slope
- Aspect
- Rainfall-related features
- Land cover
- Additional geological features where reliable data is available

## Structure

- `data/raw` — Original downloaded datasets
- `data/external` — External GIS/raster datasets
- `data/processed` — Processed training datasets
- `notebooks` — Exploratory analysis
- `src/data` — Data loading and cleaning
- `src/features` — Feature engineering
- `src/models` — Model training
- `src/evaluation` — Model evaluation
- `models` — Saved trained models

## Current Stage

Phase 3 — Dataset collection and ML pipeline development.
