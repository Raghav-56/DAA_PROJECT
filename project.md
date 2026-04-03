# Multi-Strategy E-Commerce Product Ranking System

## 1. Problem Statement

Design an extensible product ranking system for an e-commerce platform that supports multiple ranking strategies and efficiently retrieves Top-K products from large product datasets.

The system must:

- Rank products using multiple attributes.
- Support configurable ranking strategies.
- Produce explainable ranking output.
- Compare strategies on runtime and output quality.

## 2. Objectives

- Efficient Top-K retrieval on large static datasets (10^5 to 10^6 products).
- Support multiple ranking paradigms (score-based, rule-based, and multi-objective).
- Handle trade-offs between quality and runtime.
- Provide user-profile-driven customization of ranking behavior.
- Keep design modular for future extension.

## 3. Scope and Assumptions

### In Scope

- Product ranking for a given query/category filter.
- Strategy-specific Top-K retrieval.
- Benchmarking and comparison of strategies.
- Explanation generation for ranked outputs.

### Out of Scope (Current Version)

- Online learning of weights.
- Real-time stream updates.
- Distributed serving infrastructure.

### Assumptions

- Dataset is static during one benchmark run.
- Required product attributes are available and cleaned.
- Missing values are imputed during preprocessing.

## 4. Dataset Specification

- Type: Structured e-commerce catalog (Amazon/Flipkart-like schema).
- Scale: 10^5 to 10^6 products, a very large dataset for offline analysis.
- Refresh mode: Batch/static for offline analysis.

### Product Representation

```text
Product = {
 id: int,
 category: str,
 price: float,
 rating: float,
 discount: float,
 delivery_time: float,
 reviews_count: int
}
```

### Attribute Orientation

Two modes of attribute orientation:

- Higher is better
- Lower is better

Attributes to order by:

- rating
- discount
- reviews_count
- price
- delivery_time

## 5. Functional Requirements

- FR-1: The system shall support multiple (at least 4) ranking strategies.
- FR-2: The system shall return Top-K products for any valid K.
- FR-3: The system shall output per-product explanation for score-based ranking.
- FR-4: The system shall benchmark all strategies on the same dataset and K.
- FR-5: The system shall support user-profile-based weight presets.

### 5.1 Edge-Case Handling Contract

| Scenario | Required behavior |
| --- | --- |
| `k <= 0` | Reject request with validation error. |
| `k > available_products` | Return all available products and report `effective_k = available_products`. |
| Empty input after filtering | Return empty list with metadata reason `no_candidates`. |
| Duplicate product `id` | `strict`: fail run. `lenient`: keep first occurrence and report duplicate count. |
| Missing required attribute | Impute if policy exists, otherwise drop product and record reason. |
| Non-finite numeric values (`NaN`, `Inf`) | Treat as missing, then impute or drop per policy. |
| Invalid domain values (`price < 0`, `delivery_time < 0`) | `strict`: fail validation. `lenient`: clamp to 0 and report correction count. |
| All products dropped in preprocessing | Return empty list with preprocessing summary. |
| All active feature weights become 0 | Fall back to deterministic ordering by `id` ascending and include warning metadata. |

## 6. Non-Functional Requirements

- NFR-1: Runtime should remain practical for 10^5 products.
- NFR-2: Strategy modules must be plug-and-play.
- NFR-3: Output should be deterministic for same input and configuration.
- NFR-4: Benchmark reports must be reproducible.

## 7. System Architecture

### Pipeline

1. Data Preprocessing
2. Strategy Selection
3. Ranking Engine
4. Top-K Retrieval
5. Explanation Generator
6. Evaluation and Reporting

### Module Interfaces

```text
rank(products, k, config) -> ranked_products
explain(product, config) -> explanation_dict
evaluate(results_by_strategy) -> metrics_table
```

### 7.1 Runtime Configuration Schema

All ranking runs must use one validated configuration object.

```yaml
version: 1
strategy: weighted            # weighted | lexicographic | pareto | hybrid
k: 100
seed: 42
data_mode: strict             # strict | lenient
attributes:
  - name: rating
    direction: benefit        # benefit | cost
    weight: 0.35
    required: true
  - name: price
    direction: cost
    weight: 0.25
    required: true
  - name: discount
    direction: benefit
    weight: 0.15
    required: false
  - name: delivery_time
    direction: cost
    weight: 0.15
    required: false
  - name: reviews_count
    direction: benefit
    weight: 0.10
    required: false
normalization:
  method: minmax
  epsilon: 1e-12
  clip_quantiles: [0.01, 0.99]
  constant_feature_policy: drop_and_renormalize   # drop_and_renormalize | neutral_0_5
  skew_transform:
    reviews_count: log1p
topk:
  method: auto                # auto | heap | quickselect
  require_sorted_output: true
  deterministic_quickselect: true
tie_break:
  score_epsilon: 1e-9
  keys: [final_score, rating, reviews_count, discount, price, delivery_time, id]
  order: [desc, desc, desc, desc, asc, asc, asc]
pareto:
  mode: auto                  # exact | approximate | auto
  max_exact_n: 200000
  prefilter_multiplier: 20
  epsilon_dominance: 0.0
reproducibility:
  fixed_seed: true
  single_thread: true
  stable_sort: true
```

Validation rules:

- `k` must satisfy `1 <= k <= filtered_product_count` at runtime (or be auto-reduced with metadata).
- Weights are required for `weighted` and `hybrid`, with `weight >= 0` and `sum(weight) = 1 +/- 1e-9`.
- Product `id` must be unique.
- Unknown strategy names or unknown attributes must fail validation.

## 8. Ranking Strategies

### 8.1 Weighted Scoring

#### Weighted Idea

Convert multi-attribute product data into one comparable scalar score.

#### Weighted Formula

```text
Score(P) = sum(i=1..m) [w_i * f_i(P)]
where sum(w_i) = 1 and f_i(P) are normalized features
```

#### Weighted Steps

1. Normalize each feature into [0, 1].
2. Apply inverse transform for cost attributes.
3. Multiply by weights and sum.
4. Retrieve Top-K using heap or sort.

#### Weighted Pseudocode

```text
for each product P:
  s = 0
  for each active feature i:
    s += w_i * normalized_feature_i(P)
  keep (s, P) in size-k min-heap

extract heap to list
stable-sort by comparator: (-score, -rating, -reviews_count, -discount, price, delivery_time, id)
return sorted list
```

#### Weighted Complexity

- Scoring: O(n * m)
- Top-K with min-heap: O(n log k)
- Full ranking via sort: O(n log n)

### 8.2 Lexicographic Sorting

#### Lexicographic Idea

Rank by strict priority order of attributes.

Example priority:

1. rating (desc)
2. price (asc)
3. delivery_time (asc)

#### Lexicographic Complexity

- O(n log n)

#### Lexicographic Trade-off

- Very fast and interpretable.
- Sensitive to priority order and ignores weak-signal attributes.

### 8.3 Pareto-Optimal Ranking (Multi-Objective)

#### Pareto Idea

Avoid collapsing all objectives into one score. Product A dominates B if:

- A is no worse than B in all objectives.
- A is strictly better in at least one objective.

#### Pareto Output

- Non-dominated front (Front-1), then subsequent fronts for deeper ranking.

#### Pareto Complexity

- Naive pairwise dominance check: O(n^2 * m)

#### Pareto Trade-off

- High solution quality for multi-objective decisions.
- Expensive for very large n without approximation.

### 8.4 Hybrid Strategy

#### Hybrid Idea

1. Compute Pareto fronts.
2. Apply weighted score within each front.
3. Merge fronts in order, preserving within-front score order.

#### Hybrid Benefit

- Reduces bias of pure weighted scoring.
- Better quality-runtime balance than full Pareto-only ranking.

### 8.5 Pareto Scalability Strategy

Use mode-based execution to keep Pareto ranking practical at large `n`.

Mode selection (`n` = candidate count after filtering):

- `n <= 50000`: exact non-dominated sorting.
- `50000 < n <= max_exact_n` (default `200000`): exact block-wise skyline with pruning.
- `n > max_exact_n`: approximate Pareto with controlled error.

Exact block-wise strategy:

1. Presort by one benefit attribute (desc) and one cost attribute (asc).
2. Process products in blocks (default `20000`) to compute local non-dominated sets.
3. Merge local fronts incrementally and prune dominated points early.
4. Stop generating additional fronts once at least `k` items are collected, unless full ranking is requested.

Approximate strategy:

1. Prefilter to `M = min(n, prefilter_multiplier * k, 100000)` using weighted proxy score.
2. Apply epsilon-dominance bucketing (`epsilon_dominance`, default `0.01`).
3. Run exact front computation on survivors.
4. Report approximation metadata: `prefiltered_n`, `survivor_n`, `epsilon_dominance`.

## 9. Top-K Retrieval Design

### 9.1 Preferred: Min-Heap

```text
Initialize empty min_heap
For each product P:
 s = score(P)
 push (s, P)
 if heap_size > K:
  pop minimum
Return heap elements sorted descending by score
```

#### Min-Heap Complexity

- O(n log k)

#### Min-Heap Use Case

- Best when K is much smaller than n.

### 9.2 Alternative: QuickSelect Threshold

- Expected O(n) to find K-th score threshold.
- Followed by filtering candidates >= threshold.
- Useful when K is a large fraction of n.

### 9.3 Deterministic Tie-Breaking Policy

To satisfy deterministic output requirements, every strategy must use a total ordering key and stable sort.

Strategy primary ordering:

- Weighted: `final_score` descending.
- Lexicographic: configured attribute priority order.
- Pareto: `front_index` ascending.
- Hybrid: `front_index` ascending, then within-front score descending.

Global fallback key:

- `id` ascending is mandatory as the final tie-break key.

Floating-point tie handling:

- Treat two scores as equal when `abs(a - b) <= score_epsilon` (default `1e-9`).
- Round computed scores to 12 decimal places before comparison.
- Use a stable sorting algorithm for final ordering.

Required comparator tuple for weighted and hybrid within-front ranking:

```text
(-final_score, -rating, -reviews_count, -discount, price, delivery_time, id)
```

### 9.4 Auto Rule for Top-K Method (Heap vs QuickSelect)

Define `r = k / n`, where `n` is the number of scored candidates.

Auto-selection rule:

1. If `n < 50000`, use heap.
2. If `r <= 0.10`, use heap.
3. If `r >= 0.30`, use quickselect.
4. If `0.10 < r < 0.30`, run a one-time 2% sample micro-benchmark and choose the faster method.
5. If strict reproducibility is enabled and deterministic quickselect is disabled, force heap.

Quickselect correctness requirements:

- Pivot selection must be deterministic (median-of-three or median-of-medians).
- Select threshold score first, then include all items above threshold.
- If threshold ties exceed remaining slots, resolve with deterministic tie-break comparator.
- If sorted output is required, perform a stable sort on the final selected set before return.

## 10. Normalization and Feature Engineering

### Min-Max Scaling

```text
norm(x) = (x - min_x) / max(max_x - min_x, epsilon)
```

### Inverse for Cost Attributes

```text
benefit_transform(x) = 1 - norm(x)
```

Applied to:

- price
- delivery_time

### Data Quality Handling

- Missing numerical values: median imputation.
- Outliers: optional winsorization or clipping.

### 10.1 Normalization Edge Cases

Normalization pipeline:

1. Apply domain cleanup and optional quantile clipping.
2. Apply skew transforms (default: `log1p` for `reviews_count`).
3. Compute min and max from non-missing values.
4. Normalize with epsilon-safe denominator.
5. Clamp normalized values to `[0, 1]`.
6. For cost attributes, apply `1 - norm(x)`.

Edge-case rules:

- Zero-variance feature (`max_x - min_x <= epsilon`): mark feature inactive and renormalize remaining weights.
- If all features become inactive: skip score-based ordering and use deterministic fallback ordering.
- Missing values after preprocessing: median imputation per attribute; if median is unavailable, drop product.
- Discount unit mismatch (`0..1` vs `0..100`): auto-detect and convert to `0..1` before normalization.
- For Pareto dominance checks, use orientation-corrected values; normalized values are for within-front scoring and explanations.

## 11. User-Profile Weight Customization

| Feature | New Customer | Returning Customer | Premium Customer |
| --- | --- | --- | --- |
| Price | High | Medium | Low |
| Rating | Medium | High | High |
| Delivery Time | Low | Medium | High |
| Discount | High | Medium | Low |

Implementation detail:

- Convert qualitative levels to numeric weights.
- Normalize to ensure sum(w_i) = 1.

Example conversion (`High=3`, `Medium=2`, `Low=1`) for New Customer over `[price, rating, delivery_time, discount]`:

- Raw vector: `[3, 2, 1, 3]`
- Sum: `9`
- Normalized weights: `[0.3333, 0.2222, 0.1111, 0.3333]`

## 12. Explainability Specification

For each ranked product, return:

- Final score
- Per-feature contribution
- Human-readable reason summary

### Explanation Output Format

```text
Product ID: 1023
Final Score: 0.81

Contribution Breakdown:
- rating: +0.45
- price: +0.20
- discount: +0.10
- delivery_time: +0.06

Reason:
High rating and competitive price increased this product's rank.
```

## 13. Strategy Comparison Module

### Metrics

1. Execution time (ms)
2. Top-K overlap between strategies
3. Score distribution statistics
4. Diversity of selected products

### Overlap Metric

```text
Overlap(A, B) = |TopK_A intersect TopK_B| / K
```

Tie handling for overlap comparison:

- Overlap uses product IDs after deterministic tie-breaking has been applied.
- If strategies return fewer than K items, compute overlap on `effective_k`.

### Example Report Table

| Strategy | Time (ms) | Notes |
| --- | --- | --- |
| Weighted | 120 | Balanced baseline |
| Lexicographic | 95 | Fast, priority-sensitive |
| Pareto | 800 | Quality-focused, expensive |
| Hybrid | 300 | Practical quality trade-off |

## 14. Complexity Summary

| Component | Time Complexity |
| --- | --- |
| Normalization | O(n * m) |
| Weighted Scoring | O(n * m) |
| Heap Top-K | O(n log k) |
| Full Sort Ranking | O(n log n) |
| Pareto (naive) | O(n^2 * m) |
| Hybrid (front + score) | Dominated by Pareto step |

Where:

- n = number of products
- m = number of attributes
- k = requested Top-K size

## 15. Optimization Techniques

- Use heap-based Top-K instead of full sort when k << n.
- Vectorize scoring computations.
- Use approximate Pareto front for large n.
- Cache normalized features for repeated queries.
- Parallelize strategy runs for benchmarking.

## 16. Extensibility Design

### Strategy Plug-In Contract

```text
class RankingStrategy:
 name: str
 def rank(products, k, config):
  pass
```

### Extension Points

- Add new product attributes with normalization adapters.
- Add new ranking strategy implementing same interface.
- Add custom evaluator metrics without changing ranking logic.

## 17. Evaluation Plan

1. Use same dataset split and K for all strategies.
2. Run each strategy multiple times.
3. Record mean runtime and variance.
4. Compare overlap and diversity metrics.
5. Analyze qualitative differences in Top-K outputs.

## 18. Testing and Reproducibility Requirements

### 18.1 Minimum Test Suite

- Unit tests for scoring, normalization, imputation, tie-breaking, and Top-K selection.
- Edge-case tests for empty input, `k` boundaries, duplicate IDs, zero-variance features, and all-missing attributes.
- Strategy correctness tests on toy datasets with known expected outputs.
- Regression tests with golden Top-K product ID lists for fixed dataset/config pairs.
- Property-style tests for monotonicity on benefit and cost attributes.

### 18.2 Reproducibility Protocol

- Record dataset hash (for example, SHA-256 of input data).
- Record config hash (for example, SHA-256 of canonicalized config).
- Record source version (git commit ID if available).
- Record runtime environment (Python version, dependency lock, OS, CPU metadata).
- Use fixed seed and deterministic settings for all benchmark runs.
- Run each benchmark at least 5 times and report mean, standard deviation, and p95 runtime.
- Acceptance criterion: same dataset hash and config hash must produce identical ordered Top-K product IDs.
- Include preprocessing statistics (imputed count, dropped count, corrected count) in benchmark reports.
