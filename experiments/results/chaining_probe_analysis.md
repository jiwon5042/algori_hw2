# Separate chaining probe experiment

Reproduce with `make experiment`. The run uses capacity 1,000, a fixed random seed (2026), and 64-bit keys; it records all inserted keys for successful lookups. For unsuccessful lookups it selects one absent key for each bucket, so the bucket sample is balanced.

| Load factor | Keys | Successful measured / theory | Unsuccessful measured / theory |
| ---: | ---: | ---: | ---: |
| 0.25 | 250 | 1.132 / 1.125 | 0.250 / 0.250 |
| 0.50 | 500 | 1.258 / 1.250 | 0.500 / 0.500 |
| 0.75 | 750 | 1.367 / 1.375 | 0.750 / 0.750 |
| 1.00 | 1000 | 1.506 / 1.500 | 1.000 / 1.000 |
| 1.25 | 1250 | 1.622 / 1.625 | 1.250 / 1.250 |
| 1.50 | 1500 | 1.759 / 1.750 | 1.500 / 1.500 |
| 1.75 | 1750 | 1.857 / 1.875 | 1.750 / 1.750 |
| 2.00 | 2000 | 1.972 / 2.000 | 2.000 / 2.000 |
| 2.25 | 2250 | 2.106 / 2.125 | 2.250 / 2.250 |
| 2.50 | 2500 | 2.237 / 2.250 | 2.500 / 2.500 |
| 2.75 | 2750 | 2.369 / 2.375 | 2.750 / 2.750 |
| 3.00 | 3000 | 2.501 / 2.500 | 3.000 / 3.000 |
| 3.25 | 3250 | 2.625 / 2.625 | 3.250 / 3.250 |
| 3.50 | 3500 | 2.762 / 2.750 | 3.500 / 3.500 |
| 3.75 | 3750 | 2.884 / 2.875 | 3.750 / 3.750 |
| 4.00 | 4000 | 3.006 / 3.000 | 4.000 / 4.000 |

The successful-search measurements track `1 + alpha/2`; the largest absolute difference in this deterministic run is 0.028 at alpha=2.00. Small differences are expected because the formula is an expectation and this run uses a finite key set. The unsuccessful-search values equal alpha because the experiment probes every bucket once; this balanced sampling is intentional and should not be mistaken for a random-query estimate.

The CSV table and SVG graph are generated beside this report.
