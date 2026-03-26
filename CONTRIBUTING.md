# Contributing

Thanks for your interest in improving B1 Pipeline.

## Before you change anything

Please keep in mind what this repository is and is not:

- It is a research/engineering project for semi-automatic stock selection.
- It is not an automated trading bot.
- It is not a promise of profitability.

## Recommended contribution areas

High-value directions include:

- feature engineering improvements
- ranking/scoring calibration
- test coverage improvements
- performance optimization
- documentation and usability improvements
- safer configuration handling

## Development setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Or with editable install flow:

```bash
pip install -e .
pip install pytest
```

## Running tests

```bash
pytest tests
```

## Practical guardrails

Please avoid:

- committing real API tokens
- committing local `data/` snapshots
- committing local logs or private experiment files
- making large rule changes without sample-case validation

## Suggested workflow

1. create a branch
2. make a focused change
3. run relevant tests
4. update docs if behavior changes
5. open a pull request with a concise explanation

## Documentation expectations

If you change any of the following, update docs too:

- daily run workflow
- configuration format
- review output shape
- fetch / preprocess behavior
- scoring logic assumptions
