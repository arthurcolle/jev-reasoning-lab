# Advanced Jev experiments — actual executed results

**220 successful requests / 285 typed answers**, pinned `jev-1.13.0`. Estimated inference **$0.007012**; conservative reservation $0.059952. Coordinator cost unknown. No retries and no real deployments, payments, SSH jobs or account actions.

## 1. Can Jev investigate before answering?

Twelve eight-hypothesis worlds expose seven exact tests with different costs and a five-unit test budget. Jev chooses a test; the local simulator returns its actual hidden-world observation; that observation changes the next model call. A commit is counted only if all remaining consistent hypotheses agree—not merely if a guess happens to match the hidden world.

- Initial unguided Jev: **1/12 verified diagnoses**; 11 abstentions.
- Greedy information-gain reference: **10/12** identified. This reference is not claimed globally optimal.
- Many model episodes stopped before buying any information. One stopped even after its observations uniquely identified the answer. This is a planning/control failure, not an unsafe real-world action.

### Fresh paired follow-up

After observing that failure, we added a deterministic remaining-hypothesis ledger and exposed only affordable informative probes, with computed information gain. The controller—not Jev—commits on uniqueness and stops when no information can be bought. Twelve **new** worlds used the same generation family:

| Arm | Verified diagnoses |
|---|---:|
| Unguided Jev | 0/12 |
| Ledger + constrained Jev selector + deterministic termination | 12/12 |
| Deterministic greedy reference | 12/12 |

The combined system fixes the observed failure, but the deterministic reference already achieves the same completion count. **This does not establish that adding Jev improves an exactly solvable planner.** The intervention changes both visible information and allowed actions; it is not a clean prompt-only causal effect.

## 2. Belief revision over 18 dependent turns

Three paired episodes deliver new facts, explicit retractions and stale lower-version events. Each arm sees prior state and its own earlier model decisions. Readiness can move proceed → block → hold → proceed. Previous model answers are never evidence.

| Memory arm | Correct turns | Mean serialized state bytes | API input tokens |
|---|---:|---:|---:|
| Full event history + prior model decisions | 44/54 | 669 | 36821 |
| Host-maintained latest-version ledger + last decision | 53/54 | 258 | 26844 |

The ledger improves this pilot while reducing payload size. These are serialized-state bytes, not measured C-harness RSS. There are only three correlated episodes per arm, and the memory representations also differ in how much prior model output is retained.

## 3. Batching is not semantically free

Twenty-four new exact knapsack/shortest-path problems were checked with two independent local algorithms before inference. The same cases were asked individually, in batches of eight, and with each batch's order reversed.

| Presentation | Correct |
|---|---:|
| Individual | 8/24 |
| Batch of eight | 10/24 |
| Reversed batch | 13/24 |

**3/24 answers changed** between the two batch orders. This is one run per condition; provider variation and ordering effects have not been disentangled. Performance is poor enough that batching cannot be treated as a validated exact-reasoning backend.

## 4. Adversarial tool text versus typed trusted state

Twelve injection strings were paired with permitted and denied trusted states: fake administrator claims, emergency pressure, JSON-shaped overrides, fake receipts and benchmark-pressure text. Jev got **24/24** simulated decisions correct. This is a narrow synthetic check of an explicit trust boundary—not general prompt-injection security, and the output never grants a real capability.

## 5. Confidence coverage/risk

The preregistered cutoffs are descriptive on this same pilot, not independent calibration:

| Chosen probability >= | Accepted | Errors | Accuracy among accepted |
|---|---:|---:|---:|
| 0.5 | 199/204 | 51 | 74.37% |
| 0.7 | 127/204 | 16 | 87.40% |
| 0.9 | 91/204 | 1 | 98.90% |
| 0.95 | 74/204 | 1 | 98.65% |

Even very high reported probabilities retained an error. The curve mixes easy trust/state cases with difficult arithmetic, and observations share templates/episodes. Do not convert these numbers into a production confidence guarantee.

## Engineering consequence

Use Jev for bounded semantic choices where exact rules are unavailable. Keep versioned memory, legality, evidence tests, termination, arithmetic and permissions in deterministic code. Ask whether Jev adds value over a cheap reference, not whether a larger hybrid can be made to succeed.

All attempt/response hashes and raw inputs were retained in the ignored run directories. Gold labels, expected verdicts and hidden-world identity were excluded from API state. `advanced_report.py` replays grading and verifies every paid response hash. Public traces contain synthetic fixtures only. No production policy was changed.
