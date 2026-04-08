# Multi-Strategy E-Commerce Product Ranking System

## Overview

This project implements an extensible product ranking system for e-commerce platforms that intelligently ranks products based on multiple attributes and retrieves the top-K products efficiently from large datasets.

Think of it as a smart shopping assistant that shows you the best products based on what matters most to you:  
price, ratings, delivery time, discounts, or a combination of all of these.

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

This project uses the **Amazon Products Sales 42K (2025)** dataset, a curated collection of real e-commerce products with comprehensive historical sales and review information.

### Dataset Overview

- **Source**: Amazon product catalog (Kaggle, CC BY-NC 4.0 licensed)
- **Scale**: 42,000+ products  
  - Ideal for learning and benchmarking all ranking strategies  
  - Can be augmented to 100K+ with controlled resampling for scalability studies
- **Attributes**: 
  - **Required**: Price, rating (0–5 stars)
  - **Optional**: Discount percentage, review count, category, delivery estimates
- **Type**: Static batch dataset (offline analysis), snapshots of products across all categories

### Data Quality

- **Coverage**: Multiple product categories (Electronics, Books, Home & Kitchen, etc.)
- **Preprocessing**: Single-table structure minimizes data wrangling complexity
- **Interpretability**: Real e-commerce prices and ratings, results are immediately applicable

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

## Example: Ranking Smartphones

Here's how different strategies rank the same 6 smartphones:

### Original Catalog

``` txt
Product            | Price   | Rating | Delivery | Reviews
─────────────────────────────────────────────────────────────
Smartphone A       | ₹14,999 | 4.2    | 2 days   | 850
Smartphone B       | ₹11,999 | 4.5    | 4 days   | 910
Smartphone C       | ₹14,999 | 4.0    | 3 days   | 620
Smartphone D       | ₹8,999  | 4.1    | 1 day    | 700
Smartphone E       | ₹11,999 | 4.7    | 2 days   | 980  ← Best overall
Smartphone F       | ₹19,999 | 4.6    | 5 days   | 760
```

### Strategy 1: Weighted Scoring (Price 30%, Rating 40%, Reviews 20%, Delivery 10%)

``` txt
1. Smartphone E    ✓ High rating, good price, fast delivery, popular
2. Smartphone B    ✓ Good rating, competitive price
3. Smartphone A    ✓ Good rating and reviews, moderate price
4. Smartphone F    ~ Excellent rating, but expensive & slow
5. Smartphone D    ~ Cheapest, but lower rating
6. Smartphone C    ✗ Lowest rating
```

### Strategy 2: Lexicographic (Sort by: Rating → Price → Delivery)

``` txt
1. Smartphone E    (4.7 rating, cheapest among top-rated)
2. Smartphone F    (4.6 rating, but expensive)
3. Smartphone B    (4.5 rating, good price)
4. Smartphone A    (4.2 rating)
5. Smartphone D    (4.1 rating, cheapest overall)
6. Smartphone C    (4.0 rating, slowest)
```

### Strategy 3: Pareto-Optimal (Multi-objective balance)

``` txt
Front-1 (Non-dominated):
  - Smartphone E (best rating + good price + fast)
  - Smartphone B (fast + high popularity)
  - Smartphone F (highest rating)

Front-2:
  - Smartphone A (ratings, delivery, reviews)
  - Smartphone D (lowest price)

Front-3:
  - Smartphone C (dominated by all)
```

### Strategy 4: Hybrid (Pareto fronts + weighted score within each)

``` txt
Front-1 ordered by weighted score:
1. Smartphone E
2. Smartphone F
3. Smartphone B

Front-2 ordered by weighted score:
4. Smartphone A
5. Smartphone D

Front-3:
6. Smartphone C
```

See [project.md](project.md) for the complete technical specification and detailed evaluation metrics.

## Project Structure

``` txt
case_study/
├── project.md       # Full technical specification
├── README.md        # This file
└── (implementation files will go here)
```
