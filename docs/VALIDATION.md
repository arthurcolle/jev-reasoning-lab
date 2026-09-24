# Extraction validation

Verified locally with Python 3.14 and the dependency versions pinned in `pyproject.toml`:

- Eight offline unit tests passed, including all 128 saved exact-atom cases, malformed-input abstention, strict probability validation, explicit live opt-in and bounded mock frontier calls.
- All five notebooks executed successfully with live mode disabled, credentials removed from the test environment, and Python socket connection attempts blocked. No notebook attempted a network call. The five portable notebooks retain no execution outputs or execution counts. The separate root historical notebook intentionally retains its saved outputs and counts and is not executed in offline validation.
- The wheel built successfully in an isolated build environment, retained the imported MIT notice, and passed an import/exact-peer smoke test from its extracted installation directory.
- Curated shareable files were checked for private home paths, original fleet identifiers, private IP ranges, private-key blocks and common credential-token formats. This is a useful review, not a guarantee against every possible secret format.
- Original research notebooks, projects and running sessions were not edited by extraction. Headless validation kernels were shut down.

No paid Jev evaluation was run during packaging. Historical benchmark summaries are explicitly historical. API examples remain opt-in and use the reader's own credentials.

The source research's failed reviewer closeouts and experimental limitations are not turned into a clean production certification here. This repo is an experiment lab, not a production routing or psychological-assessment product.
