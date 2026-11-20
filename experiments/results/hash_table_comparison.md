Repository: https://github.com/jiwon5042/algori_hw2

# Linear probing and chaining comparison

Separate chaining stores colliding keys in a linked list at their home bucket. Linear probing stores each key in its own array cell and scans forward from the home cell when a collision occurs.

Reproduce with `make experiment`. Both tables have capacity 1,000 and receive the same seeded 64-bit keys at each load factor. Successful searches visit every stored key once; unsuccessful searches use the same 5,000 seeded absent-key queries for both implementations. Linear-probing counts include the final empty cell examined on a miss.

Theory: chaining successful `1 + alpha/2`, unsuccessful `alpha`; linear probing successful `0.5 * (1 + 1/(1-alpha))`, unsuccessful `0.5 * (1 + 1/(1-alpha)^2)`.

| alpha | n | Chain success measured/theory | Chain miss measured/theory | Linear success measured/theory | Linear miss measured/theory |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.1 | 100 | 1.070/1.050 | 0.093/0.100 | 1.080/1.056 | 1.117/1.117 |
| 0.2 | 200 | 1.100/1.100 | 0.196/0.200 | 1.110/1.125 | 1.267/1.281 |
| 0.3 | 300 | 1.163/1.150 | 0.295/0.300 | 1.210/1.214 | 1.583/1.520 |
| 0.4 | 400 | 1.222/1.200 | 0.398/0.400 | 1.407/1.333 | 2.024/1.889 |
| 0.5 | 500 | 1.258/1.250 | 0.495/0.500 | 1.574/1.500 | 2.863/2.500 |
| 0.6 | 600 | 1.293/1.300 | 0.593/0.600 | 1.842/1.750 | 3.990/3.625 |
| 0.7 | 700 | 1.327/1.350 | 0.694/0.700 | 2.216/2.167 | 6.037/6.056 |
| 0.8 | 800 | 1.417/1.400 | 0.792/0.800 | 3.185/3.000 | 14.561/13.000 |
| 0.9 | 900 | 1.473/1.450 | 0.892/0.900 | 6.060/5.500 | 36.086/50.500 |

The chaining successful-search maximum absolute difference in this run is 0.023; the linear unsuccessful-search maximum absolute difference is 14.414. Differences from the formulas are expected-value sampling effects. At alpha=0.9, linear probing averages 36.086 miss probes against the 50.500 expected value: the 5,000 queries measure this one table, whose finite cluster layout is not the average over independently built tables. Linear probing's unsuccessful cost rises sharply as the table fills because primary clusters make long runs of occupied cells more likely; separate chaining grows approximately linearly with alpha.

The SVG contains separate successful/unsuccessful panels. The two-page PDF summarizes the setup, formulas, data, and measured curves.

## Agent errors and how they were caught

A server test first used a URL pair that did not actually collide at the table's capacity. The missing chain arrow exposed the mistake; checking both Horner indices found a colliding pair and the test then passed.

I also treated a successful localhost response as proof that the Codespaces browser URL was available. Checking the forwarded URL separately showed that its port was not forwarded, so local and external responses must be verified independently.
