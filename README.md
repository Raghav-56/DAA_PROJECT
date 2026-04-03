# Multi-Strategy E-Commerce Product Ranking System

## Overview

This project implements an extensible product ranking system for e-commerce platforms that intelligently ranks products based on multiple attributes and retrieves the top-K products efficiently from large datasets.

Think of it as a smart shopping assistant that shows you the best products based on what matters most to yo:price, ratings, delivery time, discounts, or a combination of all of these.

## Key Features

### 4 Ranking Strategies

1. **Weighted Scoring**: Combines multiple product attributes with customizable weights. Fast and balanced.
2. **Lexicographic Sorting**: Ranks by strict priority order (e.g., "highest rating first, then lowest price"). Quick and interpretable.
3. **Pareto-Optimal Ranking**: Multi-objective approach that avoids trade-offs. Best quality, slower execution.
4. **Hybrid Strategy**: Combines Pareto fronts with weighted scoring for practical quality-runtime balance.

### Smart Customization

- **User Profile Modes**: Different weight presets for new customers, returning customers, and premium members.
- **Explainable Results**: Each ranked product includes a breakdown of why it was selected.
- **Benchmark & Compare**: Measure performance and result quality across all strategies.

## The Data

- **Scale**: 100,000 to 1,000,000 products
- **Attributes**: Rating, price, discount, delivery time, review count, category
- **Type**: Static batch dataset (offline analysis)

## What It Does

1. **Preprocess**: Clean and prepare product data
2. **Rank**: Apply one of four strategies to order products
3. **Retrieve Top-K**: Get the best N products efficiently
4. **Explain**: Show why each product ranked where it did
5. **Evaluate**: Compare strategies on speed, quality, and overlap

## Design Highlights

- Modular architecture: Easy to add new ranking strategies
- Scalable: Handles large datasets with practical runtimes
- Deterministic: Same input always produces same output
- Reproducible: Full audit trail with dataset/config hashes

## Quick Stats

| Metric | Performance |
| --- | --- |
| Small Dataset (10K) | ~50-100 ms |
| Medium Dataset (100K) | ~120-800 ms (strategy dependent) |
| Large Dataset (1M) | Optimized for practical runtimes |

See [project.md](project.md) for the complete technical specification.

## Project Structure

``` txt
case_study/
├── project.md       # Full technical specification
├── README.md        # This file
└── (implementation files will go here)
```

## Next Steps

Implement ranking engines and evaluation harness based on the detailed specification in `project.md`.
