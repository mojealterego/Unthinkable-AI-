# Cain's Jawbone — evidence workbench (source D7)

Input: "Analiza _Żuchwy Kaina_ i Python - Google Gemini.PDF", 11 pages (user-provided). The page-boundary heuristic is described on pp. 1–3, TF-IDF/TTR and K-Means on pp. 4–8, and optional local LLM adapter on pp. 8–11.

## Implemented here
- Non-probabilistic ranking of candidate page adjacency based on syntactic punctuation/case and boundary lexical overlap.
- Validated JSON corpus interface, 1..100 page IDs, no bundled book text.
- Reproducible stylometric features (TTR, word length, punctuation density).
- Optional exploratory TF-IDF + K-Means (scikit-learn/numpy), **not** narrator identification proof.
- Deterministic unit tests; CSV/JSON output is inspectable and includes the explicit \`solved: false\`.

Run:

    python -m services.cain.jawbone /path/to/user-supplied-pages.json --top 5
    python -m unittest discover -s tests -p 'test_cain_solver.py' -v

## Reliability and limitations
Original source calls scores \`0.85\` and \`0.15\` "probability" despite providing no calibration dataset; this implementation deliberately avoids that claim. The source's example uses *three* K-Means groups despite its narrative proposing six narrators and hardcodes centroid distance to 0.0. Those are not reproduced as scientific facts.

The historical assertion "exactly 12 people" cannot be verified from the provided document and should not appear as a definitive current statistic. More importantly, this PDF does **not** contain the full 100 pages from the novel, so no actual ordering, solution, murderer list or experimental accuracy is claimed.

Real acceptance: an authorized full corpus; source citation per page; independent linguistic/historical crosschecks; human verification; held-out examples and optional literature references. Do not commit copyrighted corpus without distribution rights.
