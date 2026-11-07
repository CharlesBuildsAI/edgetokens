# EdgeTokens publish archive manifest (2026-11-06)
Source: /workspace/edgetokens (unchanged). Data: 242 benchmark rows, 23 boards; site/ is latest local build (site/data CSVs identical to data/).
File list with sha256/size: MANIFEST-files.txt.
## Excluded
- scripts/*.bak* (11 old backups, superseded)
- raw/ (42MB scraped third-party pages/PDF, copyright; regenerable from source URLs)
- preview/*.png (49MB QA screenshots; preview scripts kept in tools/preview/)
- edgetokens-site.zip (older 233-row deploy bundle)
- newsletter/, launch/ (marketing drafts, not site source; flagged for user decision)
- No .git, .env, wrangler/cloudflare config present.
## Scan
grep regex for api keys/secret/token=/password/bearer/sk-/ghp_/AKIA/PEM/cloudflare/wrangler/emails/local paths: 0 findings. Public Amazon affiliate tag kept (557 occurrences).
## After import (2026-11-07)
Imported into CharlesBuildsAI/edgetokens. Archive sha256: `af17c647feaec7266742b8e13ab5201120732c0645097febe403a6422a9e2f2e` (203 files). `MANIFEST-files.txt` checksums are for that archive. Files changed after import, so they no longer match those checksums: `README.md`, `scripts/check_links.py`, `tools/preview/shoot.py`, `tools/preview/shoot_kits.py`, `tools/preview/shoot_apple.py`, and this file. `.gitignore` was added and is not in the archive. The packaging note above (`/workspace/edgetokens`) is the machine path the archive was packed from. Preview scripts now write under `preview/` relative to the repo root.
