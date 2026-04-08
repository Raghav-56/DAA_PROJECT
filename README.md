# E-Commerce Top-K Product Ranking: Proof of Concept

## Overview

This project implements a minimal proof-of-concept for efficient product ranking using three sorting algorithms (Merge Sort, Quick Sort, Heap Top-K) on 42,000 real e-commerce products. It delivers two components: a production-ready ranking API server with caching, and a comprehensive benchmarking analysis of algorithm performance.

## Objectives

1. **Ranking Server Software** (Component A): Production-ready HTTP API accepting ranking requests and returning sorted product IDs with optional caching.
2. **Benchmarking & Performance Analysis** (Component B): Benchmark suite measuring runtime, complexity, and scalability across all algorithm-strategy combinations.

---

## Core Deliverables

### Component A: Ranking Server Software

**HTTP API** (`POST /rank`) accepting ranking requests with strategy, algorithm, and k parameters. Returns sorted product IDs with execution metrics. Implements LRU caching with configurable TTL.

**Implementation stack**: FastAPI + Uvicorn.

**Supported ranking strategies**: Single-Attribute Ascending/Descending, Lexicographic, Weighted Composite Score.  
**Algorithms**: Merge Sort (O(n log n)), Quick Sort (O(n log n) avg), Heap Top-K (O(n log k)).  
**Features**: Thread-safe concurrent request handling, automatic algorithm selection, strict inactive-attribute validation with opt-in fallback, comprehensive error handling.

**Details**: See [project.md § 4](project.md#4-server-architecture--requestresponse-protocol): API specification, request/response formats, caching mechanism, configuration, error codes.

### Component B: Benchmarking & Performance Analysis

**Executes** 12 algorithm-strategy combinations across 4 dataset sizes {1K, 5K, 10K, 42K} with varying k values {10, 100, 500}.

**Protocol**: Cache disabled for benchmark warmup and measured runs; 2 warmups + 5 measured iterations per point; report mean and median for ranking-only and end-to-end timing scopes.

**Deliverables**: Raw benchmark CSVs, algorithm comparison summary, performance graphs (runtime scaling, complexity verification, speedup analysis), markdown report with findings and hardware specifications.

**Details**: See [project.md § 9](project.md#9-benchmark-design-and-validation-protocol): Methodology, validation criteria, performance profiles, output formats.

---

## Scope: What Is Included

- Python server implementation with `/rank` HTTP API
- Merge Sort, Quick Sort, Heap Top-K algorithms with deterministic comparators
- Four ranking strategies: Single-Attribute (Asc/Desc), Lexicographic, Weighted Composite
- LRU caching with configurable TTL and automatic invalidation
- Thread-safe concurrent request handling with strict-by-default fallback controls (`allow_fallback`)
- Comprehensive benchmark suite: 12 algorithm-strategy combinations × 4 dataset sizes × 3 k-values = 144+ runs
- Performance metrics: runtime, complexity verification, memory usage, speedup analysis
- Outputs: Raw/summary CSVs, performance graphs, markdown report with hardware details
- Reproducibility baseline: uv-managed Python 3.12 environment with pinned dependencies and committed `uv.lock`

**Details**: See [project.md § 2–3](project.md#2-algorithms-specification-and-rationale) for algorithms and ranking strategies; [§ 4](project.md#4-server-architecture--requestresponse-protocol) for server details; [§ 9–11](project.md#9-benchmark-design-and-validation-protocol) for benchmarking and execution.

## Scope: What Is Out of Scope

The following advanced topics are intentionally deferred to the Extended roadmap:

- Pareto-optimal ranking (multi-objective skyline computation)
- Hybrid strategies combining Pareto fronts with weighted scoring
- User-profile-based weight presets and customization
- Explainability and per-product rank justification
- Complex configuration validation and edge-case handling
- Multi-table ETL pipelines or advanced data wrangling

For the extended design plan, refer to `Extended/README_extended.md` and `Extended/project_extended.md`.

## Dataset

**Amazon Products Sales 42K (2025)**  
**Source**: [Kaggle](https://www.kaggle.com/datasets/ikramshah512/amazon-products-sales-dataset-42k-items-2025)  
**License**: CC BY-NC 4.0 (academic research use; non-commercial)  
**Scale**: 42,000+ products in single CSV table  
**Core attributes**: price (cost), rating (benefit)  
**Optional attributes**: discount, reviews_count, delivery_time, category

**Feature activation**: Core attributes always active. Optional attributes active iff present in dataset AND >95% parsing success AND statistically significant (variance > 1e-12).

**Data quality**: Missing values <30% per attribute; price and rating mandatory; median imputation for missing numeric values.

**Details**, candidate evaluation, and schema mapping: See [dataset.md](dataset.md)

## Ranking & Algorithms

**Deterministic total order** enforced across all three algorithms:

- Primary: Composite score (descending) or single attribute (ascending/descending) per strategy
- Tie-breaks are strategy-specific (see project spec), with deterministic final fallback on product_id (asc) then row_uid (asc)
- Floating-point tolerance: scores equal iff |a - b| ≤ 1e-9

**Algorithm specifications, preprocessing formulas, scoring computations**: See [project.md § 2, 6–7](project.md#2-algorithms-specification-and-rationale)

## References

- **[project.md](project.md)**: Technical specification: algorithms, ranking strategies, server API, benchmarking protocol, preprocessing formulas, deterministic comparators, execution/invocation details
- **[dataset.md](dataset.md)**: Dataset research, candidate evaluation, schema mapping, preprocessing validation, ETL considerations
- **[links.md](links.md)**: Dataset URLs and repository links
- **[Extended/](Extended/)**: Advanced features roadmap and archived original specification (Pareto ranking, multi-strategy frameworks, extended reproducibility)

## Setup and Reproducibility

All commands are `uv`-based for deterministic environments.

```bash
uv sync
```

This installs runtime and dev dependencies from `pyproject.toml` and creates `uv.lock`.

Optional dependency operations:

```bash
uv add <package>
uv add --dev <package>
```

## Run API Server

```bash
uv run uvicorn Src.api.app:app --host 0.0.0.0 --port 5000
```

Health check:

```bash
uv run curl http://localhost:5000/health
```

## Run Benchmarks

Smoke benchmark (fast subset):

```bash
uv run python Src/main.py benchmark --smoke
```

Full benchmark matrix:

```bash
uv run python Src/main.py benchmark --full
```

## Run Tests

Smoke tests:

```bash
uv run pytest -m smoke -v
```

Full suite:

```bash
uv run pytest -v
```

## Output Artifacts

Default output directories:

- `outputs/benchmarks/benchmark_results.csv`
- `outputs/rankings/*.json`
- `outputs/reports/benchmark_report.md`
- `outputs/reports/runtime_scaling.png`
- `outputs/reports/algorithm_comparison.png`
- `outputs/reports/speedup_analysis.png`
- `outputs/reports/validation_*.md`
