# EdgeTokens

EdgeTokens is a sourced leaderboard of LLM tokens per second on small boards: Raspberry Pi, NVIDIA Jetson, Rockchip, Hailo, and Axera. Every published speed is transcribed from a public source URL stored on the same row. The name means those measured tokens per second.

The dataset in this repository is the local build with **242 benchmark rows** and **23 board/price rows**. The generated homepage reports 242 measured runs, 17 boards and configs, 44 models, and 20 public sources. https://edgetokens.dev was still serving an older 233-run build when this snapshot was packed. This repository does not deploy the site, change DNS, or connect hosting.

## What is source, and what is generated

| Path | Role |
| --- | --- |
| `data/benchmarks.csv` | Source dataset. 242 rows. Each row has `source_name`, `source_url`, `source_date`, and `date_type`. |
| `data/boards.csv` | Source price list. 23 rows. 16 have a price and a price-source URL. 7 say `price not verified` and have no price URL. |
| `scripts/build_data.py` | Regenerates both CSVs. Most numbers are transcribed in the script. The Rockchip RK3588 and RK3576 block reads `raw/rkllm_main.md`. |
| `scripts/build_site.py` | Regenerates `site/` from the CSVs plus `scripts/style.css` and `scripts/app.js`. Python standard library only. |
| `scripts/accessories.py` | Accessory catalog (ASINs, Seeed product URLs, non-Amazon prices) used by the generator. |
| `site/` | Generated static site (178 pages, including the copied CSVs, CSS, and JS). Edit the scripts, then regenerate. Do not hand-edit `site/`. |
| `tools/preview/` | Optional Playwright screenshot scripts. They write under `preview/` at the repo root. |
| `screenshot-*.png` | Three screenshots of an earlier 233-run leaderboard. They are historical captures. They do not match the current `site/`. |
| `MANIFEST.md`, `MANIFEST-files.txt` | Checksums and exclusion list for the 2026-11-06 archive this tree was imported from. |

`site/data/*.csv` is a copy of `data/*.csv`. `site/assets/style.css` and `site/assets/app.js` are copies of `scripts/style.css` and `scripts/app.js`.

## Build and preview

Requirements: Python 3. No third-party packages are required to regenerate or serve the site.

```bash
python3 scripts/build_site.py
cd site && python3 -m http.server 8765
```

Open http://127.0.0.1:8765/ . `BASE_URL` in `scripts/build_site.py` is already `https://edgetokens.dev` and is used for canonical URLs, `sitemap.xml`, and `robots.txt`.

To regenerate the CSVs as well:

```bash
mkdir -p raw
curl -fsSL -o raw/rkllm_main.md \
  https://raw.githubusercontent.com/airockchip/rknn-llm/f7390530443bf84f0394255a449d7cbe81e69d1c/benchmark.md
python3 scripts/build_data.py
python3 scripts/build_site.py
```

`raw/` is gitignored. It is the Rockchip `benchmark.md` at the commit already cited in the CSV. This repo does not vendor that third-party file. With that file present, `build_data.py` reproduces `data/benchmarks.csv` and `data/boards.csv` exactly. Without it, the script stops before writing, and the committed CSVs remain the dataset to use.

`python3 scripts/build_site.py` alone reproduces `site/` byte for byte from the committed CSVs and front-end sources.

## Checks

```bash
python3 scripts/check_links.py
```

That checks affiliate-link shape, that every accessory in `scripts/accessories.py` is linked, that the kit and guide pages are in the nav and sitemap, and that each unique Seeed shop URL returns HTTP 200. It does not crawl the open web.

`python3 scripts/check_links.py --amazon` re-fetches each accessory ASIN. `python3 scripts/asin_check.py ASIN` is the same kind of one-off Amazon fetch and writes the HTML under `raw/asin/` (gitignored). Skip both unless you intend to hit Amazon.

The preview scripts need [Playwright](https://playwright.dev/python/) and a Chrome binary at `/usr/bin/google-chrome`, plus a local server on port 8765 (`shoot.py`, `shoot_apple.py`) or `BASE` (default `http://localhost:8766` for `shoot_kits.py`). They are not part of the site build. Screenshots land in `preview/`, which is gitignored.

## Public affiliate parameters

These are public link parameters in the generated HTML, kept on purpose. They are not credentials.

- Amazon Associates tag `edgetokens-20` (`AMAZON_TAG` in `scripts/build_site.py`).
- Seeed Studio `sensecap_affiliate=WwUWAV9&referring_service=link` (`SEEED_AFF`).

Some boards have no verified Amazon product page, so the generator emits a tagged Amazon search URL instead of an `/dp/ASIN` link. Amazon prices are never printed. Accessory prices come from Seeed Studio, Samsung, and Arace Tech, with the source URL and the date 2026-10-17.

## Still open

The old README listed `NEWSLETTER_PROVIDER_PLACEHOLDER`, `SUBMIT_BACKEND_PLACEHOLDER`, and empty affiliate slots. Those strings are not in this tree. What is actually still unfinished:

- **Newsletter.** The footer form posts to Buttondown's public embed endpoint `https://buttondown.com/api/emails/embed-subscribe/edgetokens`. There is no API key in the repo. This import does not create or verify that Buttondown account.
- **Submissions.** `/submit/` does not post to a backend. It opens a prefilled GitHub issue on `CharlesBuildsAI/edgetokens`. The confirmation text says to email "the newsletter address" if you have no GitHub account, and no address is configured.
- **Prices.** These seven board rows have no verified price: M5Stack AI Pyramid, M5Stack LLM8850, Jetson Orin NX 8GB, Jetson Orin NX 8GB Super, Jetson Orin NX 16GB, Jetson Orin NX 16GB Super, and Arduino UNO Q 4GB.
- **Screenshots.** `screenshot-home.png`, `screenshot-board-rpi5.png`, and `screenshot-can-rpi5-llama.png` show the earlier 233-run pages (the hero says 233 measured runs). `site/index.html` is the 242-run build.
- **License.** There is no `LICENSE` file in this repository.

## Left out of the archive

Kept out on purpose, and not re-added here: `scripts/*.bak*` backups, the `raw/` third-party page and PDF snapshot, the bulk `preview/*.png` QA shots, the older `edgetokens-site.zip` 233-row bundle, and `newsletter/` plus `launch/` marketing drafts. No `.env`, wrangler, or Cloudflare config was in the archive.
