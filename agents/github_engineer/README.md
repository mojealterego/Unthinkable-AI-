# GitHub maintenance worker

A scheduled GitHub Actions worker polls the most recent results on `main` of the Flutter smoke build, specification validation, and trace integrity validation. It opens one deduplicated issue per currently failing workflow. Runs every four hours and supports manual dispatch. Uses scoped `GITHUB_TOKEN`, Python standard library, bounded HTTP timeouts and no external AI provider.

This is a **real CI health monitor**, not an autonomous programming system or DGM. It never auto-merges, deploys, changes files, reads secrets, assumes a CI pass, or closes human-owned issues. Future coding capability needs a separately implemented proposal worker, sandbox verification, review and rollback gate.
