# Jev Reasoning Lab

A clean, portable version of the Jev notebook: typed decisions, model-lane hypotheses, reasoning-lens selection, structural variants, numeric recurrence findings, and a terse tool-grounded adversarial peer.

**Original notebook, with all saved cells and results:** [jev_api_test.ipynb](jev_api_test.ipynb)
**Static HTML, also with saved results:** [jev_api_test.html](jev_api_test.html)

The full notebook retains its original cell order and execution outputs, with private infrastructure identifiers redacted. It is a historical executed snapshot, not an offline Run All target. The smaller `notebooks/` files below are separate portable, offline-by-default demos—not replacements for the original.

## Setup

Python **3.14+** is required by the pinned `jev` package.

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[notebooks]'
jupyter lab
```

The five portable notebooks under `notebooks/` run **offline by default**. The root historical notebook preserves its original live cells; see its opening warning. To deliberately run paid TypeSafe examples, export your own key and opt in **before launching Jupyter**:

```sh
export TYPESAFE_API_KEY='YOUR_OWN_KEY'
export JEV_LAB_LIVE=1
jupyter lab
```

Do not commit your key, `.env`, private inputs or run logs. Copying `.env.example` alone does not automatically load it; environment exports are the documented path. Running every live tutorial cell can make multiple paid requests. This notebook guard is not a provider billing cap or a sandbox.

## Notebooks

1. **Jev API:** decorators, typed questions, async, batching, score bounds and local type-safety checks.
2. **Routing and lenses:** cheap/strong recommendations and the portable 18-lens client. The routing example does not execute the selected language model; relative costs are illustrative.
3. **Decision surface:** receipts, retrieval/consistency examples and A/B variants. Fleet profiles are fictional; there is no SSH or fleet dispatch.
4. **Results and peer:** historical empirical results and an offline exact-tool peer demo. No paid inference is needed.
5. **Numeric frontier:** an explicit-opt-in, call-bounded portable recurrence/branching demo; historical runs are not replayed automatically.

## What the evidence says

More reasoning/debiasing prompts did not reliably improve this synthetic pilot. The first intervention sweep repaired 78 wrong answers but harmed 79 correct ones. Exact tools helped on their supported problems; model-judged confidence did not become a verifier.

The peer accepts explicit supported atoms. It does not verify arbitrary free-text extraction, source authenticity, or real-world truth. It grants no permissions and executes no external actions. The 750 candidate strategy–target pairs are not an established top-750 efficacy ranking, and LLMs are not assumed to share human psychological mechanisms.

## Check locally

```sh
python -m unittest discover -s tests -v
```

The test suite makes no paid calls. Notebook validation is described in `docs/VALIDATION.md` after local verification.

## Scope of this split

Included: portable tutorial content, small standalone Python components, synthetic exact-tool fixtures, and sanitized aggregate results.

Excluded: credentials, actual machine addresses, SSH key material/configuration, actual private filesystem paths, raw private conversations, DSCO's native runtime/router implementation and git history. The root historical notebook retains fleet example code and recorded outputs, with private identifiers redacted; the portable demos perform no fleet dispatch. Native C Jev routing remains in DSCO; this repository is the shareable research lab, not a claim that all DSCO routing technology has been extracted.

Original notebooks and projects remain untouched. See `LICENSE_SCOPE.md` for retained notices and the pending repository-wide license decision. The repository is published on GitHub. No collaborator invitation was needed for public viewing.
