# Minimal Proof-of-Concept: Technical Specification

## 1. Objective

Implement two integrated deliverables:

**Component A: Ranking Server Software** - A production-ready HTTP API server that accepts ranking requests from clients, applies selected sorting algorithms, and returns sorted product IDs. The server includes a caching layer to avoid redundant computations.

**Component B: Benchmarking & Performance Analysis** - A comprehensive benchmark suite that evaluates the performance of all algorithm-strategy combinations across multiple dataset sizes and k values, producing runtime data, complexity analysis, and comparative visualizations.

The implementation shall prioritize clarity, reproducibility, and deterministic output over advanced optimization.

## 2. Algorithms: Specification and Rationale

### 2.1 Merge Sort (Full Ranking)

**Purpose**: Baseline stable sort ensuring correct total ordering independent of input permutation.  
**Time Complexity**: O(n log n) in all cases (best, average, worst).  
**Space Complexity**: O(n) for auxiliary merge buffer.  
**Stability**: Guaranteed: equal elements maintain relative input order.  
**Applicability**: Suitable for full dataset ranking when complete ordering is required.

**Implementation Constraint**: Merge Sort must use a stable comparator (see Section 5) to ensure deterministic output. Floating-point tie-breaking rules must be applied consistently during all comparisons.

### 2.2 Quick Sort (Full Ranking)

**Purpose**: Evaluate average-case performance with careful pivot selection to ensure reproducibility.  
**Time Complexity**: O(n log n) average case; O(n²) worst case if pivot selection is adversarial.  
**Space Complexity**: O(log n) for recursive call stack (in-place partition).  
**Stability**: Not guaranteed by standard implementation, but tie-breaking rules ensure reproducibility.  
**Applicability**: Tests whether average-case speed advantage justifies added algorithmic complexity.

**Deterministic Pivot Strategy**: Use median-of-three (first, middle, last elements) to reduce worst-case probability and ensure reproducible behavior across runs. Do not use random pivot selection.

### 2.3 Heap-based Top-K (Selective Ranking)

**Purpose**: Efficient retrieval when K << N (e.g., Top-100 from 42K products).  
**Time Complexity**: O(n log k) for finding Top-K; O(k log k) to output sorted Top-K.  
**Space Complexity**: O(k) for min-heap storage.  
**Applicability**: Preferred when K is small relative to dataset size and full ranking is not required.

**Implementation Detail**: Use a min-heap of size k; process all products; extract heap and sort output to maintain comparator consistency with sort-based approaches.

## 3. Ranking Methods and Strategies

The system must support multiple distinct ranking strategies that determine HOW products are scored and ordered. Each strategy defines a different approach to computing product priority.

### 3.1 Available Ranking Strategies

The PoC shall implement at minimum the following four ranking strategies:

#### Strategy A: Single-Attribute Ascending

**Configuration**: `{strategy: "single_asc", attribute: "rating"}` or attribute ∈ {price, rating, discount, reviews_count, delivery_time}  
**Behavior**: Rank products by ONE attribute in ascending order (lower values first).  
**Use Case**: "Show me cheapest products first" or "Show fastest delivery first".  
**Example**: attribute=price → sorts products lowest price to highest.  
**Deterministic Tie-Break**: If two products have equal primary attribute, apply strategy-specific deterministic tie-break rules (Section 7.1), ending with product_id then row_uid.

#### Strategy B: Single-Attribute Descending

**Configuration**: `{strategy: "single_desc", attribute: "rating"}` or attribute ∈ {price, rating, discount, reviews_count, delivery_time}  
**Behavior**: Rank products by ONE attribute in descending order (higher values first).  
**Use Case**: "Show me highest-rated products first" or "Show biggest discounts first".  
**Example**: attribute=rating → sorts products highest rating to lowest.  
**Deterministic Tie-Break**: Same as Strategy A, applied to remaining rows with equal primary attribute.

#### Strategy C: Lexicographic (Multi-Attribute Priority Order)

**Configuration**: `{strategy: "lexicographic", priority: ["rating", "price", "reviews_count"]}` where priority is an ordered list of attributes.  
**Behavior**: Sort by first attribute (descending if benefit, ascending if cost); use second attribute as tie-breaker, then third, etc.  
**Use Case**: "I care most about rating, then secondarily about price, then about reviews".  
**Example**: priority=[rating desc, price asc, reviews_count desc] → highest rating first; if tied on rating, lowest price; if tied on both, highest reviews.  
**Deterministic Tie-Break**: Works naturally; final keys are product_id ascending, then row_uid ascending.

#### Strategy D: Weighted (Composite Score)

**Configuration**: `{strategy: "weighted", weights: {"rating": 0.40, "price": 0.30, "discount": 0.15, "reviews_count": 0.10, "delivery_time": 0.05}}` where weights are normalized to sum to 1.0.  
**Behavior**: Compute composite score as weighted sum of normalized features (Section 4.3); rank by composite score descending.  
**Use Case**: "Balance all factors equally" or custom business logic with specific weight preferences.  
**Manual Configuration Example**: User can override weights; system renormalizes to sum = 1.0.  
**Deterministic Tie-Break**: Applies full tie-break chain (Section 5.1) for products with equal composite score.

### 3.2 Strategy Selection and Input Contract

Each ranking execution must specify EXACTLY ONE strategy via a configuration input. The configuration object specifies:

```
RankingConfig = {
  strategy: str,           // one of ["single_asc", "single_desc", "lexicographic", "weighted"]
  strategy_params: dict    // strategy-specific parameters
}
```

**Examples**:

- `{strategy: "single_desc", strategy_params: {attribute: "rating"}}` → Rank by rating descending
- `{strategy: "weighted", strategy_params: {weights: {rating: 0.5, price: 0.5}}}` → Rank by 50% rating + 50% price
- `{strategy: "lexicographic", strategy_params: {priority: ["rating", "price"]}}` → Rank by rating, then price

### 3.3 Feature Availability and Fallback

If a selected ranking strategy references an attribute that is inactive (missing from dataset or non-significant per Section 3.3 data contract), the system shall:

1. If `allow_fallback=false` (default), return HTTP 400 and include `inactive_attributes` in the error payload.
2. If `allow_fallback=true`, log a warning: "Attribute {X} not available; using fallback strategy".
3. Fall back to weighted strategy using only active attributes (renormalize weights).
4. Return HTTP 200 with `metadata.fallback_applied=true`.

## 4. Server Architecture & Request/Response Protocol

The Ranking Server Software component is a production-ready HTTP API that handles client requests for on-demand product ranking.

### 4.1 Server Design Overview

**Architecture**: Stateless HTTP server with optional in-memory caching layer.

**Technology Stack**:

- Framework: FastAPI (Python)
- ASGI Server: Uvicorn
- Data handling: Pandas (preprocessing), NumPy (array operations)
- Concurrency: Uvicorn worker process model
- Caching: LRU cache with configurable size limits

**Thread Safety**: All ranking operations are thread-safe; cache updates use atomic operations.

### 4.2 HTTP API Endpoint: `/rank`

**Method**: `POST`  
**Content-Type**: `application/json`

#### Request Format

```json
{
  "strategy": "weighted",
  "strategy_params": {
    "weights": "default"
  },
  "algorithm": "quick_sort",
  "k": 100,
  "return_fields": ["product_id", "primary_score", "score_type", "rating", "price"],
  "allow_fallback": false,
  "use_cache": true
}
```

**Request Parameters**:

| Field | Type | Required | Valid Values | Description |
|---|---|---|---|---|
| `strategy` | string | Yes | "single_asc", "single_desc", "lexicographic", "weighted" | Ranking strategy to apply |
| `strategy_params` | object | Yes | (varies by strategy) | Strategy-specific parameters (see Section 3.2) |
| `algorithm` | string | No | "merge_sort", "quick_sort", "heap_top_k", "auto" | Sorting algorithm. Explicit non-auto values are always honored. Default "auto" uses deterministic rule: if k > 0.3n then quick_sort, else if k ≤ 1000 then heap_top_k, else quick_sort |
| `k` | integer | No | 1 to 42000 | Number of top products to return; default 100. If k exceeds effective rows after preprocessing, k is clamped and reported in metadata |
| `return_fields` | array | No | ["product_id", "primary_score", "score_type", "ranking_keys", "rating", "price", "discount", "reviews_count", "delivery_time"] | Attributes to include in response; default ["product_id", "primary_score", "score_type"] |
| `allow_fallback` | boolean | No | true/false | Controls inactive-attribute behavior; default false returns HTTP 400, true enables weighted fallback |
| `use_cache` | boolean | No | true/false | Enable caching; default true |

**Score Semantics**:

- `score_type="weighted_composite"` → `primary_score` is weighted composite score
- `score_type="single_attribute"` → `primary_score` is selected raw attribute value
- `score_type="lexicographic"` → `primary_score=null`; ordered key values are returned in `ranking_keys`

#### Response Format

**Success Response (HTTP 200)**:

```json
{
  "status": "success",
  "algorithm_used": "quick_sort",
  "strategy": "weighted",
  "k": 100,
  "ranked_products": [
    {
      "product_id": 12345,
      "primary_score": 0.942,
      "score_type": "weighted_composite",
      "rating": 4.8,
      "price": 299.99,
      "discount": 25.0
    },
    {
      "product_id": 67890,
      "primary_score": 0.918,
      "score_type": "weighted_composite",
      "rating": 4.7,
      "price": 349.99,
      "discount": 15.0
    }
  ],
  "execution_metrics": {
    "algorithm_time_ms": 12.5,
    "total_time_ms": 13.2,
    "cache_hit": false,
    "cache_key": "hash_abc123def456"
  },
  "metadata": {
    "timestamp": "2026-04-08T14:23:45.123Z",
    "dataset_rows_used": 42000,
    "effective_k": 100,
    "fallback_applied": false,
    "active_features": ["rating", "price", "discount", "reviews_count"],
    "active_weights": {
      "rating": 0.424,
      "price": 0.318,
      "discount": 0.159,
      "reviews_count": 0.106
    }
  }
}
```

**Error Response (HTTP 400/500)**:

```json
{
  "status": "error",
  "error_code": "invalid_strategy",
  "message": "Strategy 'foo' not recognized. Valid options: single_asc, single_desc, lexicographic, weighted",
  "timestamp": "2026-04-08T14:23:45.123Z"
}
```

**Error Codes**:

- `invalid_strategy`: Strategy not in allowed set
- `missing_required_param`: Required parameter missing
- `invalid_algorithm`: Algorithm not in ["merge_sort", "quick_sort", "heap_top_k", "auto"]
- `attribute_not_found`: Requested field in return_fields does not exist
- `inactive_attribute_unavailable`: Requested strategy references inactive attributes and `allow_fallback=false`
- `internal_error`: Server error during processing (HTTP 500)

### 4.3 Caching Mechanism

**Cache Key**: SHA-256 hash of `(strategy, canonical_strategy_params_json, algorithm, k)` to ensure uniqueness. Canonical strategy params serialization uses sorted keys, no extra whitespace, and stable numeric formatting.

**Cache Entry Structure**:

```python
{
  "key": "abc123...",
  "ranked_products": [...],
  "execution_metrics": {...},
  "created_at": 1712599425.123,
  "hits": 5
}
```

**Eviction Policy**: LRU (Least Recently Used) when max cache size exceeded.

**Cache Parameters** (configurable):

- `max_cache_size_mb`: 100 (default), max memory for cached results
- `cache_ttl_seconds`: 3600 (default), time-to-live per entry
- `enable_cache`: true (default)

**Cache Invalidation**:

- Auto-invalidate: When dataset file is reloaded/updated (detected via file hash)
- Manual: Server endpoint `POST /cache/clear` to flush cache (admin token required)
- Partial: `POST /cache/clear/{strategy}` to clear entries for specific strategy (admin token required)

### 4.4 Server Configuration

**Configuration File** (JSON):

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "workers": 4
  },
  "dataset": {
    "path": "./data/amazon_42k.csv",
    "reload_on_change": true
  },
  "cache": {
    "enabled": true,
    "max_size_mb": 100,
    "ttl_seconds": 3600,
    "admin_token": "${CACHE_ADMIN_TOKEN}"
  },
  "preprocessing": {
    "imputation_strategy": "median",
    "normalization_method": "minmax",
    "random_seed": 42
  },
  "algorithms": {
    "heap_preferred_k_threshold": 1000,
    "quick_sort_fraction_threshold": 0.30,
    "median_of_three_threshold": 100
  }
}
```

### 4.5 Fallback & Error Handling

**Invalid Strategy Parameters**: Return HTTP 400 with clear error message.

**Missing Attributes**: If strategy references unavailable attribute (e.g., delivery_time missing):

1. If `allow_fallback=false` (default), return HTTP 400 with inactive attribute list.
2. If `allow_fallback=true`, log warning with attribute name and reason (missing/inactive).
3. Apply fallback strategy: weighted with active features only.
4. Renormalize weights across active set.
5. Return HTTP 200 with `"fallback_applied": true` in metadata.

**Concurrency Handling**: Thread-safe request queuing with configurable worker pool. Max queue size prevents memory exhaustion.

---

## 5. Input Data Contract

### 5.1 Dataset Source

- **Name**: Amazon Products Sales 42K (2025)
- **Expected Row Count**: 42,000 (±5% tolerance for dataset updates)
- **Format**: Single CSV table with 11–15 columns
- **Required Columns**: product_rating, discounted_price
- **Optional Columns**: product_id, discount_percentage, total_reviews, delivery_date, product_category

If `product_id` is missing, the system shall generate deterministic synthetic product IDs from row_uid using format `row_000001`.

### 5.2 Feature Set and Mapping

The system operates on five product attributes with the following orientation:

| Attribute | Dataset Column | Type | Orientation | Default Weight |
|---|---|---|---|---|
| rating | product_rating | float ∈ [0.0, 5.0] | Benefit (↑ better) | 0.40 |
| price | discounted_price | float (₹) | Cost (↓ better) | 0.30 |
| discount | discount_percentage | float ∈ [0, 100] | Benefit (↑ better) | 0.15 |
| reviews_count | total_reviews | int ≥ 0 | Benefit (↑ better) | 0.10 |
| delivery_time | delivery_date | float (days) | Cost (↓ better) | 0.05 |

### 5.3 Feature Activation Rules

**Mandatory Features**: `price` and `rating` must be present and non-degenerate.  
**Optional Features**: `discount`, `reviews_count`, `delivery_time` are active only if:

1. **Present**: Column exists in the input CSV.
2. **Significant**: Feature has non-zero variance across products (> 1e-12 range).
3. **Parseable** (delivery_time only): Delivery date values are converted to numeric days with >95% success rate.

If an optional feature fails any of these checks, it is marked inactive; weights are renormalized across active features (see Section 5.2).

## 6. Preprocessing and Scoring

### 6.1 Data Cleaning Pipeline

1. **Type Coercion**: Parse all numeric columns to float or int as appropriate; treat parse errors as missing values.
2. **Missing Value Handling**: Flag `NaN`, `Inf`, and `None` as missing. For each active numeric feature, impute missing values with the column median computed over non-missing values.
3. **Validation**: Drop any row where price or rating remains missing after imputation; log dropped-count in preprocessing summary.
4. **Row Identity and Duplicate Handling**: Retain all rows; create internal `row_uid` from original row index as stable deterministic tie-break key when product IDs are non-unique.
5. **Product ID Handling**: If `product_id` is absent, generate deterministic synthetic IDs using `row_{row_uid:06d}`.

### 6.2 Normalization and Feature Engineering

**Min-Max Scaling** (applied to each active feature independently):

$$
\text{norm}(x) = \frac{x - \min(x)}{\max(x) - \min(x) + \epsilon}
$$

where $\epsilon = 1\text{e-}12$ to avoid division by zero for constant features.

**Benefit vs. Cost Adjustment**: For cost-oriented attributes (`price`, `delivery_time`), apply inverse transform:

$$
\text{benefit}(x) = 1 - \text{norm}(x)
$$

For benefit-oriented attributes (`rating`, `discount`, `reviews_count`), use normalized value directly.

### 6.3 Composite Score Computation

After normalization, the composite product score is computed as:

$$
\text{Score}(P) = \sum_{i \in A} w'_i \cdot f_i(P)
$$

where:

- $A$ = set of active features
- $w'_i$ = renormalized weight for feature $i$
- $f_i(P)$ = normalized (and possibly inverted) feature value for product $P$

**Weight Renormalization**: Given default base weights (rating 0.40, price 0.30, discount 0.15, reviews_count 0.10, delivery_time 0.05), compute active weights:

$$
w'_i = \frac{w_i^{\text{base}}}{\sum_{j \in A} w_j^{\text{base}}}
$$

**Edge Case**: If all features become inactive (unlikely but covered for robustness), fall back to deterministic ordering by product ID ascending.

### 6.4 Strategy-Specific Score Computation

For **single-attribute strategies** (ascending/descending):

- No normalization required; use raw attribute values directly for comparison
- Optionally normalize for reporting purposes

For **lexicographic strategy**:

- Each attribute in the priority list is compared independently; no normalization needed
- Use raw attribute values with semantic orientation (ascending for cost, descending for benefit)

For **weighted strategy**:

- Normalization is mandatory (Section 6.2)
- Weight renormalization applies based on active features (Section 6.3)

## 7. Deterministic Output Specification

### 7.1 Total Ordering Comparator

All three algorithms must respect a total order on products. The order depends on the selected ranking strategy:

#### For Single-Attribute Strategies

**Primary Key**: Selected attribute value (ascending or descending per strategy)  
**Tie-Break Sequence**:

1. Product ID (ascending)
2. row_uid (ascending), final deterministic key

#### For Lexicographic Strategy

**Primary Key**: First attribute in priority list (oriented by attribute type)  
**Tie-Break Sequence**: Remaining attributes in priority order, then product ID, then row_uid  

#### For Weighted Strategy

**Primary Key**: Composite score (descending)  
**Tie-Break Sequence** (in order, if earlier keys are equal) for weighted:

1. rating (descending): prefer higher rating
2. discount (descending): prefer higher discount (if active)
3. reviews_count (descending): prefer higher review count (if active)
4. price (ascending): prefer lower price
5. delivery_time (ascending): prefer faster delivery (if active)
6. product_id (ascending)
7. row_uid (ascending), final deterministic break

### 7.2 Floating-Point Comparison

Two scores are considered equal (for tie-breaking purposes) if:

$$
|\text{score}_a - \text{score}_b| \leq 1\text{e-}9
$$

Round all computed scores to 12 decimal places before comparison to minimize floating-point accumulation errors.

### 7.3 Reproducibility Guarantees

Given identical input data (same CSV file, same row order) and identical configuration (same active features, same base weights), implementations must produce:

- Identical Top-K product IDs in identical order for any K
- Identical complete ranking order for the full 42K dataset
- Identical scores (up to floating-point rounding) for each product

Differences in wall-clock runtime are expected but not order-related.

## 8. Algorithm Implementation Details

### 8.1 Merge Sort Pseudocode

```
Function MergeSort(products, comparator):
  if products.length <= 1:
    return products
  
  mid = products.length / 2
  left = MergeSort(products[0:mid], comparator)
  right = MergeSort(products[mid:], comparator)
  
  return Merge(left, right, comparator)

Function Merge(left, right, comparator):
  result = new List
  i, j = 0, 0
  
  while i < left.length and j < right.length:
    if comparator(left[i], right[j]) <= 0:  // stable: take left on equal
      result.append(left[i])
      i += 1
    else:
      result.append(right[j])
      j += 1
  
  result.append(left[i:])  // append remaining
  result.append(right[j:])
  return result
```

**Key Property**: Merge operation is stable; equal elements preserve input relative order.

### 8.2 Quick Sort with Deterministic Pivot

```
Function QuickSort(products, low, high, comparator):
  if low < high:
    pivot_idx = Partition(products, low, high, comparator)
    QuickSort(products, low, pivot_idx - 1, comparator)
    QuickSort(products, pivot_idx + 1, high, comparator)

Function Partition(products, low, high, comparator):
  median_idx = MedianOfThree(products, low, low+(high-low)/2, high, comparator)
  Swap(products[median_idx], products[high])
  pivot = products[high]
  
  i = low - 1
  for j in range(low, high):
    if comparator(products[j], pivot) < 0:
      i += 1
      Swap(products[i], products[j])
  
  Swap(products[i + 1], products[high])
  return i + 1

Function MedianOfThree(products, a, b, c, comparator):
  if comparator(products[a], products[b]) < 0:
    if comparator(products[b], products[c]) < 0:
      return b  // a < b < c
    elif comparator(products[a], products[c]) < 0:
      return c  // a < c <= b
    else:
      return a  // c <= a < b
  else:
    if comparator(products[a], products[c]) < 0:
      return a  // b <= a < c
    elif comparator(products[b], products[c]) < 0:
      return c  // b < c <= a
    else:
      return b  // c <= b <= a
```

### 8.3 Heap-based Top-K

```
Function HeapTopK(products, k, comparator):
  if k >= products.length:
    return Sort(products, comparator)
  
  min_heap = new MinHeap(size=k, comparator=reverse(comparator))
  
  for product in products:
    if heap.size < k:
      heap.insert(product)
    elif comparator(product, heap.peek()) > 0:
      heap.extract_min()
      heap.insert(product)
  
  result = heap.extract_all()
  Sort(result, comparator)  // output must be sorted
  return result
```

**Note**: Heap is min-heap to efficiently track k largest elements. Final output is sorted using the same comparator as sort-based methods for consistency.

## 9. Benchmark Design and Validation Protocol

Benchmarking evaluates the performance of the three sorting algorithms ACROSS multiple ranking strategies. The protocol measures both runtime and output quality.

### 9.1 Benchmarking Scope

The PoC shall execute all three algorithms (Merge, Quick, Heap) with EACH of the following ranking strategies:

| Ranking Strategy | Parameters | Purpose |
|---|---|---|
| single_desc | {attribute: rating} | Test single-attribute ranking (highest first) |
| single_asc | {attribute: price} | Test single-attribute ranking (lowest first) |
| lexicographic | {priority: [rating, price, reviews_count]} | Test multi-attribute priority ordering |
| weighted | {weights: {rating: 0.4, price: 0.3, discount: 0.15, reviews_count: 0.1, delivery_time: 0.05}} | Test weighted composite score |

This creates a 3 × 4 = 12 test combinations (3 algorithms × 4 ranking strategies).

### 9.2 Benchmark Matrix

For each (algorithm, strategy) combination, execute on each dataset size:

| Algorithm | Strategy | Dataset Size | Top-K Values |
|---|---|---|---|
| Merge Sort | rating desc | {1K, 5K, 10K, 42K} | {10, 100, 500} |
| Quick Sort | rating desc | {1K, 5K, 10K, 42K} | {10, 100, 500} |
| Heap | rating desc | {1K, 5K, 10K, 42K} | {10, 100, 500} |
| [repeat for other 3 strategies] | ... | ... | ... |

### 9.3 Validation Target Datasets

Implementations must be validated on the following subsets of the primary dataset:

| Subset | Size | Purpose |
|---|---:|---|
| Small | 1,000 | Correctness check (any k) |
| Medium | 5,000 | Scaling observation |
| Large | 10,000 | Runtime trending |
| Full | 42,000 | End-to-end PoC validation |

For subset benchmarks (1K, 5K, 10K), use the first N rows from the loaded dataset. Benchmark reports shall include an explicit note that first-N selection may introduce order bias.

### 9.4 Correctness and Success Criteria

**Correctness**: Merge Sort and Quick Sort produce identical Top-K ID lists for k ∈ {10, 100, 500} on all test subset sizes.  
**Determinism**: Repeated runs return identical ranked lists.  
**Heap Consistency**: Heap Top-K output matches the first k elements from the fully sorted list (after applying tie-breaks).

All validation criteria are reported descriptively in benchmark artifacts and execution summaries; they are informational and not treated as hard pass/fail gates.

### 9.5 Benchmark Run Protocol

To improve reproducibility and comparability, each benchmark point shall be executed using the following run protocol:

1. Disable cache for warmup and measured runs.
2. Run 2 warmup iterations followed by 5 measured iterations.
3. Report both mean and median runtime values for measured runs.
4. Report two timing scopes:

- Ranking-only: strategy key preparation + ranking algorithm execution
- End-to-end: load + preprocess + score + rank + serialize

5. Runtime values are stored at full precision internally and rounded to 3 decimal places (ms) in API and benchmark outputs.

### 9.6 Expected Performance Profile by Strategy

#### Single-Attribute Strategy (rating)

Since single-attribute ranking involves no score computation, expected runtimes are the SHORTEST:

| Method | Expected Time (42K products) | Notes |
|---|---|---|
| Merge Sort | 30–80 ms | Simple attribute comparison only |
| Quick Sort | 20–60 ms | Simple pivot on single attribute |
| Heap Top-100 | 5–15 ms | Minimal overhead |

#### Lexicographic Strategy

Slightly slower due to multi-attribute comparison logic:

| Method | Expected Time (42K products) | Notes |
|---|---|---|
| Merge Sort | 40–100 ms | Multiple attribute comparisons per pair |
| Quick Sort | 30–80 ms | Multiple comparisons during partitioning |
| Heap Top-100 | 10–25 ms | Still efficient with small k |

#### Weighted Strategy

Slower due to score computation for all products:

| Method | Expected Time (42K products) | Notes |
|---|---|---|
| Merge Sort | 50–150 ms | Score computation + sorting |
| Quick Sort | 40–120 ms | Score computation + quick sort |
| Heap Top-100 | 15–40 ms | Score computation + heap selection |

*Note: Actual times depend on hardware, language (Python), data structure library performance, and whether scores are pre-computed or computed on-the-fly.*

### 9.7 Benchmark Output Formats

| Method | Expected Time (42K products) | Notes |
|---|---|---|
| Merge Sort | 50–150 ms | Stable O(n log n) |
| Quick Sort | 40–120 ms | Average-case faster; median-of-three reduces pathological inputs |
| Heap Top-100 | 15–40 ms | O(n log k) with small k |
| Heap Top-500 | 40–110 ms | Larger k reduces relative advantage |

*Note: Actual runtimes depend on hardware, language (Python), and data structure library performance.*

---

## 10. Execution and Invocation

### 10.1 Input Requirements

The implementation expects:

1. **Dataset CSV File**: Path to the Amazon 42K dataset (or subset) with the schema defined in Section 5.1
2. **Configuration Object**: A ranking strategy specification (see Section 3.2) defining which strategy to use
3. **Parameters** (optional): K value for Top-K retrieval; default k=100

### 10.2 Basic Invocation Pattern

Pseudocode for typical execution:

```python
# Load and preprocess dataset
dataset = load_csv("amazon_42k.csv")
dataset = preprocess(dataset)  # Validates, imputes, normalizes

# Define ranking strategy
config = {
    "strategy": "weighted",
    "strategy_params": {"weights": "default"}
}

# Execute all three algorithms
results = {}
for algorithm in ["merge_sort", "quick_sort", "heap_top_k"]:
    ranked_products = rank(dataset, config, algorithm, k=100)
    results[algorithm] = ranked_products

# Validate and benchmark
validate_consistency(results)  # Merge vs Quick should match
benchmark_results = measure_runtimes(results)
```

### 10.3 Configuration Specification

Each invocation must specify exactly one ranking strategy via a configuration dictionary:

```python
# Example: Rank by rating (descending)
config = {
    "strategy": "single_desc",
    "strategy_params": {"attribute": "rating"}
}

# Example: Rank by rating, then price (lexicographic)
config = {
    "strategy": "lexicographic",
    "strategy_params": {"priority": ["rating", "price"]}
}

# Example: Weighted composite score with defaults
config = {
    "strategy": "weighted",
    "strategy_params": {"weights": "default"}  # Uses rating=0.4, price=0.3, etc.
}

# Example: Weighted with custom weights (system auto-normalizes)
config = {
    "strategy": "weighted",
    "strategy_params": {"weights": {"rating": 0.5, "price": 0.5, "discount": 0.0, "reviews_count": 0.0, "delivery_time": 0.0}}
}
```

### 10.4 Output Handling

After executing all algorithm-strategy combinations:

1. Write ranked product lists to CSV/JSON (Section 11 format specifications)
2. Record wall-clock runtimes for each (algorithm, strategy, dataset_size, k) combination
3. Validate correctness (Merge vs Quick ID consistency; determinism checks)
4. Generate comparison tables and summary report

For detailed output format specifications, see Section 11 below.

## 11. Deliverable Outputs

Upon completion, the implementation shall produce:

Default output directories:

- `outputs/rankings`
- `outputs/benchmarks`
- `outputs/reports`

Default deterministic filename pattern:

- `{artifact}_{strategy}_{algorithm}_n{size}_k{k}.csv`
- `{artifact}_{strategy}_{algorithm}_n{size}_k{k}.json`

1. **Ranked Product List** (CSV or JSON)

- Columns: product_id, primary_score, score_type, [ranking_keys for lexicographic], rating, price, discount, reviews_count, [delivery_time if active], rank
- Top-100 or top-1K products sorted by final rank
- Example row: `{id: 12345, primary_score: 0.847, score_type: "weighted_composite", rating: 4.8, price: 499.99, rank: 1}`

1. **Runtime Benchmark Report** (CSV or Markdown table)

- Columns: algorithm, ranking_strategy, dataset_size, k, metric_scope, runtime_ms, mean_runtime_ms, median_runtime_ms, timestamp, notes
- One row per (algorithm, ranking_strategy, dataset_size, k) combination
- Example: `Merge Sort, weighted, 42000, 100, 87.3, 2026-04-08 14:23:00, full dataset ranked`

1. **Algorithm Comparison Table** (Markdown/CSV)
   - Rows: Algorithm names (Merge, Quick, Heap)
   - Columns: Ranking strategy, avg runtime across all dataset sizes, relative speedup vs. Merge Sort
   - Shows which algorithm is fastest for each ranking strategy
   - Example:

     ```
     | Strategy | Merge Sort (ms) | Quick Sort (ms) | Heap Top-K (ms) | Fastest |
     |---|---|---|---|---|
     | single_desc | 50 | 42 | 10 | Heap |
     | weighted | 95 | 75 | 35 | Heap |
     ```

2. **Output Artifact: Ranked Product Scores** (CSV or JSON per strategy)
   - Per ranking strategy, save Top-K product list with scores
   - Columns: product_id, primary_score, [strategy-specific attributes], rank
   - Examples:

- For `single_desc (rating)`: product_id, primary_score, score_type, rating, rank
- For `weighted`: product_id, primary_score, score_type, rating, price, discount, reviews_count, rank

1. **Correctness Validation Artifact** (per ranking strategy)

- Descriptive statement: "Strategy '{X}': Merge Sort and Quick Sort Top-K ID comparison" with mismatch_count and discrepancy list (if any)
- Descriptive statement per strategy: "Repeated runs on strategy '{X}' order consistency" with observed variation summary
- Feature activation log: "Active features: {rating, price, discount, reviews_count}; delivery_time: skipped (29% missing)"

1. **Ranking Strategy Execution Summary** (Markdown)
   - For each strategy:
     - Strategy name and configuration
     - Which algorithm was fastest and by what margin
     - Sample Top-5 products and their scores under this strategy
     - Notes on differences between strategies (e.g., "weighted strategy ranks Smartphone B higher; single_desc ranks Smartphone E higher")

2. **Implementation Summary** (README or markdown)
   - Algorithm descriptions and complexity analysis
   - Ranking strategies implemented and how to invoke them
   - Preprocessing steps applied
   - Final dataset statistics (row count, active feature count, score ranges)

- Hardware and environment info (Python version, NumPy version if used, CPU/memory profile)
- Reproducibility baseline: uv-managed Python 3.12 environment, pinned dependency versions, and committed `uv.lock`

## 12. Out of Scope

The following topics are explicitly excluded from this PoC and deferred to extended versions:

- Pareto-optimal ranking and multi-objective skylines
- Hybrid ranking combining Pareto and weighted scoring
- Advanced configuration management and YAML-based pipelines
- Per-product explainability and contribution breakdowns
- Online learning or weight adaptation
- Distributed or parallel computation
- Streaming or real-time updates
