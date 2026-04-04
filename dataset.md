# Dataset Research & Selection Process

## Research Scope & Questions

E-commerce product datasets suitable for benchmarking Top-K ranking algorithms.  

1. Datasets with product-level price, rating, discount, and reviews_count fields aligned with the core system schema
2. Datasets that support delivery_time as a cost attribute (rare in e-commerce data)
3. Benchmark scale requirements: test on 10K–100K products initially, with path to 10^5–10^6 for scalability studies
4. Evaluate preprocessing complexity: prefer single-table datasets to minimize ETL overhead
5. Confirm licensing and data quality to avoid mid-project blockers

## Core Project Schema Requirements

The ranking system expects product-level records:

``` txt
Product = {
  id: int,
  category: str,
  price: float,           # REQUIRED
  rating: float,          # REQUIRED
  discount: float,        # OPTIONAL
  delivery_time: float,   # OPTIONAL
  reviews_count: int      # OPTIONAL
}
```

**Challenges:**

- Most e-commerce datasets lack delivery_time (few have order timestamps)
- Discount is often indirect (list_price vs. selling_price, or percentage)
- Review/rating aggregation may require product-level deduplication
- Scale target (10^5–10^6) conflicts with single-table availability (<100K products rare)

## Candidate Datasets Identified & Evaluated

### Tier 1: Single-table, strong schema fit

| Dataset | Scale | Key Attributes | Problems Found | Preprocessing Effort |
|---|---:|---|---|---|
| **Amazon Products Sales 42K (2025)** | 42K items | product_rating, total_reviews, discounted_price, original_price, discount_percentage, delivery_date, product_category | Scraped data; delivery_date semantics unclear (collection vs actual delivery) | 1–2 days |
| **Cleaned Amazon Sales & Reviews** | ~11 columns | Category, pricing, review metadata | Small scale; exact field names unclear until download; possible duplicate handling | <1 day |
| **Amazon E-commerce Products & Reviews** | ~2K products, clothing | price_value, list_price, rating_stars, rating_count, delivery_date, fastest_delivery_date | Domain-specific (clothing only); single category; small scale | 1–2 days |
| **Flipkart Products (PromptCloud)** | 20K products | retail_price, discounted_price, product_rating, overall_rating, product_category_tree | **MISSING:** reviews_count field; no delivery-time signal | 1–2 days + field imputation |

**Key problems in Tier 1:**

- All single-table datasets fall short of 10^5 target scale → requires controlled resampling with fixed seed
- Delivery_date fields often ambiguous → need post-download validation
- PromptCloud Flipkart lacks reviews_count entirely → must use rating_count as proxy or exclude

### Tier 2: Multi-table, real delivery signals (medium ETL cost)

| Dataset | Structure | Delivery Signal | Key Problem | ETL Cost |
|---|---|---|---|---|
| **Olist Brazilian E-commerce** | 9 CSV tables, 52 columns total | order_purchase_timestamp → order_delivered_customer_date (real days) | Multi-table joins required; no direct product-level discount field; aggregation script required | 2–3 days |
| **DataCo Smart Supply Chain** | 1 table, 53 columns | Days.for.shipping..real. + Days.for.shipment..scheduled. (direct field) | **MISSING:** product_rating and reviews_count entirely → incompatible with weighted/lexicographic ranking | 3–4 days (low ROI) |
| **theLook Ecommerce (BigQuery)** | Synthetically-derived relational schema | order_items.created_at, shipped_at, delivered_at | **Synthetic business data** (no real user behavior); no product ratings; low external validity | Medium |

**Key problems in Tier 2:**

- Olist requires product-level aggregation via SQL joins → engineering risk, potential bugs in join logic
- DataCo delivery_time is strong but **product quality is critically weak** (no ratings/reviews) → limits which ranking strategies are testable
- theLook is synthetic mock data → results may not transfer to real e-commerce behavior

### Tier 3: Large-scale archives (very high engineering burden, deferred)

| Dataset | Scale | Why It Seemed Promising | Why Eliminated |
|---|---:|---|---|
| **Amazon Reviews 2023 (McAuley Lab)** | 571M reviews, 48M products | Can stress-test O(n) Pareto algorithms at true scale | **MISSING:** discount, delivery_time; no per-product review encoding; requires 50+ GB processing; months of ETL |
| **Amazon Reviews 2018 (UCSD)** | 233M reviews, 15.5M products | Alternative massive source | Same problems as 2023; older data quality unknown |

**Critical finding:** Large-scale datasets lack delivery_time and discount entirely. Not suitable unless project scope changes.

## Candidate Datasets

## Practical options

| Dataset | Link | Scale | Structure | Coverage vs required schema | Main caveats |
|---|---|---:|---|---|---|
| Amazon Products Sales Dataset 42K+ Items - 2025 | <https://www.kaggle.com/datasets/ikramshah512/amazon-products-sales-dataset-42k-items-2025> | 42K+ items | Single table | Has product_rating, total_reviews, discounted_price, original_price, discount_percentage, delivery_date, product_category | Not yet at $10^5$ scale by itself; scraped data cleanup needed |
| Cleaned Amazon Sales and Reviews Dataset | <https://www.kaggle.com/datasets/nadaarfaoui/cleaned-amazon-sales-and-reviews-dataset> | 1 cleaned CSV (11 columns) | Single table | Cleaned product + review/sales metadata with category/pricing/review info | Exact field names must be confirmed after download; smaller scale |
| Amazon E-commerce Products and Reviews Dataset | <https://www.kaggle.com/datasets/lazylad99/amazon-e-commerce-product-and-review-dataset> | 2 CSV files (57 columns total) | Product + review tables | Product table includes price_value, list_price, rating_stars, rating_count, delivery_date, fastest_delivery_date, category trail | Domain is clothing/accessories; row scale is moderate |
| Flipkart Products (PromptCloudHQ) | <https://www.kaggle.com/datasets/PromptCloudHQ/flipkart-products> | 20,000 products | Single table | retail_price, discounted_price, product_rating, overall_rating, product_category_tree | No direct reviews_count; no delivery-time signal |

## Schema Fit Analysis

| Dataset | price | rating | reviews_count | discount | delivery_time | category | Effort to Production | Issues |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Amazon 42K (2025) | ✓ | ✓ | ✓ | ✓ | ◐* | ✓ | **1–2 days** | Delivery_date semantics needs validation |
| Olist | ✓ | ◐** | ◐** | ✗ | ✓ | ✓ | **2–3 days** | Multi-table complexity; no discount |
| Cleaned Amazon | ✓ | ✓ | ? | ◐ | ✗ | ✓ | **<1 day** | Unknown until download; no delivery_time |
| DataCo | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | **3–4 days** | Missing core ranking attributes; low utility |
| Flipkart PromptCloud | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ | **1–2 days** | Missing reviews_count; needs proxy |

Legend: ✓ = direct; ◐ = derivable (requires processing); ✗ = missing; ? = unknown until download  
\* Derivable from delivery_date, but semantics must be verified post-download  
\** Requires product-level aggregation from order tables via SQL group-by

## 6. Licensing & Data Quality Implications

**Amazon 42K (2025):** CC BY-NC 4.0 — allows research use, prohibits commercial applications. Verifiable on Kaggle.

**Olist:** CC BY-NC-SA 4.0 — non-commercial, share-alike. Multi-table; confirmed availability (2M views in last 30 days).

**Cleaned Amazon:** Apache 2.0 — most permissive; single file reduces dependency risk.

**DataCo:** CC0/CC BY 4.0 but licensing is ambiguous on official page — recommend clarification.

**Problem identified:** All Kaggle datasets prohibit commercial publication of benchmarks. Acceptable for course deliverables, but blocks external publishing of results.

## 7. Known Issues & Validation Checklist

Before committing implementation time, must:

1. **Amazon 42K delivery_date validation:**
   - Download sample, inspect date columns
   - Verify semantics: is delivery_date observed delivery or scraped time estimate?
   - If ambiguous, fall back to synthetic generation or use product category average
   - Document exactly how derivation was chosen

2. **Product-level aggregation (Olist only):**
   - Test join logic: orders → order_items → products
   - Handle NULL delivery_customer_date (cancelled/returned orders — filter out?)
   - Decide: mean, median, or p50 for price/rating aggregation?
   - Risk: duplicate product_ids in multi-seller marketplace

3. **Scale & data count validation:**
   - Confirm Amazon 42K actually contains 42K rows (not inflated claim)
   - If using Olist, verify order count is truly ~100K

4. **Review/Rating deduplication:**
   - Amazon datasets: handle product variants and multi-seller duplicates
   - Olist: handle cross-seller products (do they aggregate or separate?)

## 8. Primary Recommendation: Amazon 42K (2025)

**Status:** SELECTED FOR V1 IMPLEMENTATION

**Rationale:**

- Single-table structure eliminates multi-table join risk
- Has all required fields (price, rating) and most optionals (discount, reviews_count, category)
- Fastest implementation path: 1–2 days from download to first benchmark run
- Active Kaggle community (verifiable downloads, user discussions)

**Schema Mapping:**

```
id                    → row index or hash(product_title + product_page_url)
category              → product_category
price                 → discounted_price
rating                → product_rating
discount              → discount_percentage / 100
reviews_count         → total_reviews
delivery_time         → DERIVED (see section 9)
```

**Delivery_time Derivation Strategy:**

- **Option A:** If delivery_date ≠ collection_date: `delivery_time = days(delivery_date - data_collected_at)`
- **Option B:** If semantics unclear: Generate synthetic category-based model (e.g., Electronics avg 3–7 days, Books avg 2–4 days)
- **Decision:** Made post-download after inspecting sample rows

**Scale:** Base 42K; for 10^5+ scale needed, resample with **fixed PRNG seed**. Document augmentation method in config.

**Next steps:**

1. Download dataset from Kaggle
2. Inspect first 100 rows + data types
3. Clarify delivery_date semantics with sample spot-check
4. Run preprocessing pipeline
5. Verify output schema against Product type

## 9. Secondary Recommendation: Olist (Optional Extension)

**Status:** SECONDARY; conditional on time availability

Applicable when:

- Real-world delivery_time behavior is needed to validate synthetic generation
- Multi-table preprocessing cost demonstration is desired
- Timeline permits 2–3 more days of engineering

**Schema Aggregation (product-level from multi-table):**

```
id                    → product_id
category              → product_category_name (translated)
price                 → median(order_items.price) grouped by product_id
rating                → mean(review_score) grouped by product_id
reviews_count         → count(distinct review_id) grouped by product_id
delivery_time         → mean(order_delivered_customer_date - order_purchase_timestamp) in days
discount              → NOT AVAILABLE (flag in config: SKIP_DISCOUNT=true)
```

**ETL Implementation Notes:**

- Filter: `WHERE order_status = 'delivered'` (exclude cancelled/pending)
- Join risk: Multi-seller products aggregate all variants together OR filter to primary seller
- Imputation: For missing delivery dates, use category median or drop rows (document choice)

## 10. Large-Scale Experiments (Defer to v2+)

**Status:** NOT RECOMMENDED FOR V1

Why Amazon 2023/2018 unsuitable:

- **Missing:** discount, delivery_time (core cost attributes)
- **Engineering burden:** 50+ GB, months of product-level aggregation
- **Scale cliff:** jumps from 100K directly to millions; no intermediate stepping stone

If you must test >1M scale:

- Filter Amazon Reviews 2023 to one category (e.g., "Electronics"): ~1.6M reviews → ~40–50K unique products (rough estimate)
- Still missing discount/delivery_time; **label as "scale-only experiment"**
- **Defer to post-V1** if timeline permits

## 11. Production Validation Checklist

Before running benchmarks:

- [ ] Download Amazon 42K dataset
- [ ] Inspect first 100 rows: confirm columns {product_rating, total_reviews, discounted_price, discount_percentage, delivery_date, product_category}
- [ ] Verify data types: price/discount as float, rating as float, reviews_count as int, dates parseable
- [ ] Sample spot-check 10 rows: what is delivery_date semantics? (future date? past date? collection date?)
- [ ] Confirm file size matches claimed 42K rows
- [ ] If using Olist: test join logic on sample data (orders → order_items → products)
- [ ] Choose delivery_time strategy and document in project README
- [ ] Run preprocessing pipeline end-to-end on sample
- [ ] Verify output columns match Product schema exactly

## 12. Summary Table: Key Findings

| Aspect | Finding | Impact | Action |
|---|---|---|---|
| **Optimal dataset** | Amazon 42K (2025) | 1–2 days to production | IMPLEMENT |
| **Delivery_time challenge** | Rare in e-commerce; mostly derived | Post-download validation required | Download & inspect |
| **Scale limitation** | 42K < 10^5 target; requires seeded resampling | Acceptable with documented approach | Fixed seed in code |
| **Licensing risk** | All Kaggle: CC BY-NC; non-commercial only | OK for course; blocks public blogs/papers | OK for course deliverable |
| **Data quality risk** | Scraped data quality unknown until download | Mitigate with early inspection | Download sample first |
| **ETL complexity** | Single-table >> multi-table by 2–3x | Strongly prefer Amazon 42K | Pick Amazon 42K |
| **Delivery_time signal strength** | Olist > DataCo > Amazon 42K (synthetic) | Trade-off speed vs realism | Use Amazon 42K for speed |

## 13. Sources & Links

1. [Amazon Products Sales 42K (2025)](https://www.kaggle.com/datasets/ikramshah512/amazon-products-sales-dataset-42k-items-2025)
2. [Cleaned Amazon Sales & Reviews](https://www.kaggle.com/datasets/nadaarfaoui/cleaned-amazon-sales-and-reviews-dataset)
3. [Amazon E-commerce Products & Reviews](https://www.kaggle.com/datasets/lazylad99/amazon-e-commerce-product-and-review-dataset)
4. [Flipkart Products (PromptCloud)](https://www.kaggle.com/datasets/PromptCloudHQ/flipkart-products)
5. [Flipkart E-commerce (Atharv Jairath)](https://www.kaggle.com/datasets/atharvjairath/flipkart-ecommerce-dataset)
6. [Olist Brazilian E-commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
7. [DataCo Smart Supply Chain](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis)
8. [theLook Ecommerce (BigQuery)](https://www.kaggle.com/datasets/mustafakeser4/looker-ecommerce-bigquery-dataset)
9. [Amazon Reviews 2023 (McAuley Lab)](https://amazon-reviews-2023.github.io/)
10. [Amazon Review Data 2018 (UCSD)](https://nijianmo.github.io/amazon/index.html)
