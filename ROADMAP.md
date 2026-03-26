# ROADMAP

## Near-term

### 1. Improve shortlist realism

Keep pushing the daily top list closer to real manual preference order.

Focus areas:

- stronger penalties for dirty pullback structure
- stronger handling of consecutive heavy-volume pullback days
- better ranking demotion for low-upside / already-ran-too-far names
- better overhead-supply modeling

### 2. Strengthen structure understanding

Important unfinished modeling frontiers:

- key-K feature explicitness
- building-wave quality modeling
- distance-to-key-K-low handling
- confluence between yellow-line support and key-K support
- long-cycle repair / box-range / low-upside penalties

### 3. Improve validation workflow

- make quick validation even cheaper to run
- improve sample-case regression checks
- keep ranking calibration tied to confirmed positive/negative anchors

## Engineering

### 1. Safer configuration

- keep secrets out of tracked config
- optionally support local private config overlays
- improve startup validation and error messages

### 2. Better project ergonomics

- add pinned dependency versions
- consider `pyproject.toml`
- improve test coverage
- add example outputs / screenshots
- improve script CLI help text

### 3. Performance

- continue optimizing fetch speed
- reduce heavy full-preprocess cost
- avoid unnecessary recomputation
- keep incremental daily path as the normal operational mode

## Sharing / open-source readiness

Before making the repository public, consider:

- another pass on secret scanning
- adding a license
- adding example config and sanitized sample outputs
- polishing contributor-facing setup instructions
