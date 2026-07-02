# Failure Analysis Notes

## Current Questions

1. Are missed ground-truth pairs missed because of embedding rank or ANN retrieval?
2. Do missed pairs still have high exact value overlap?
3. Which column profiles are associated with misses?

## Failure Labels

- `ann_failure`: exact embedding rank is high, but ANN missed it.
- `embedding_failure`: exact embedding rank is low.
- `overlap_failure`: value overlap is high, but embedding rank is low.
- `format_or_type_failure`: numeric/date/ID-like columns dominate the missed group.
- `sampling_failure`: likely caused by row sampling or truncation.
- `ground_truth_noise`: retrieved candidate appears joinable but is missing from ground truth.

