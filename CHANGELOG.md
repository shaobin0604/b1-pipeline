# CHANGELOG

## 2026-03-26

### Repository / sharing cleanup

- initialized Git repository and pushed project to GitHub
- added `.gitignore` to exclude local data, logs, caches, and virtual environments
- rewrote repository README for public/project-facing presentation
- removed hard-coded Tushare token from tracked config
- changed fetch pipeline to prefer `TUSHARE_TOKEN` environment variable
- added `.env.example` as local configuration example
- rewrote initial git history and force-pushed to remove visible token exposure from current branch history

### Pipeline / engineering state reflected in docs

- documented incremental fetch as the default daily path
- documented staged `light -> full` preprocess workflow
- documented current light-gate direction and practical operational caveats
