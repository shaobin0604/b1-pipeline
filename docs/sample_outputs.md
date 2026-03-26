# Sample Outputs

This page describes the kinds of local artifacts the pipeline produces after a daily run.

These files are normally generated under `data/` and are intentionally **not committed** to the repository.

## 1. Light candidates

Typical path:

```text
data/light_candidates/light_candidates_YYYY-MM-DD.json
```

Purpose:

- output of the first-pass light gate
- used as the input pool for heavy full preprocessing

## 2. Processed feature data

Typical paths:

```text
data/processed/
data/processed_light/
```

Purpose:

- indicator data
- merged feature tables
- intermediate structures used by preselect/review

## 3. Review input package

Typical path:

```text
data/review_input/YYYY-MM-DD/
```

May contain:

- candidate metadata
- feature snapshots
- review input JSON files

## 4. Chart exports

Typical path:

```text
data/charts/YYYY-MM-DD/
```

Purpose:

- daily chart images for manual inspection
- visual review support for shortlist confirmation

## 5. Review output

Typical path:

```text
data/review_output/YYYY-MM-DD/
```

Typical artifacts:

- scored candidate lists
- summary markdown
- ranking output for final manual review

## Notes

- The repository excludes generated `data/` by design.
- If you want to share outputs publicly, export a **sanitized sample** first.
- Do not publish private data snapshots, API secrets, or local experiment logs.
