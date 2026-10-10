# Realty AI Scout

A Flask prototype for property analysis and flip research. It combines manually
entered property facts with optional Selenium scraping, then requests a structured
analysis from Anthropic. This repository is the web interface candidate for the
investor product; the older ARV calculator and investmentpropertyanalysis projects
contain related experiments.

## Run locally

```sh
git clone https://github.com/romanee-spencer/realty-ai-scout.git
cd realty-ai-scout
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Set ANTHROPIC_API_KEY in .env
python src/app.py
```

Open http://localhost:8000 for the investor workspace. It works without API keys.
The legacy AI research form is at http://localhost:8000/research. Chrome/Chromium is needed for scraping; the scraper
attempts to obtain a driver automatically. If scraping fails, manual property
facts are still passed to the analysis. Missing API credentials prevent AI
analysis. Requests can take time while the browser and provider run.

## Current behavior

- `/` and `/investor` serve the flip-versus-rental workspace.
- `POST /strategy-comparison` calculates four flip scenarios and two rental scenarios.
- `POST /deal-analysis` calculates flip scenarios alone.
- `/research` serves the legacy AI property form.
- `POST /analyze` returns property facts, scraped comparables, and AI analysis.
- `POST /flip-analysis` returns flip research and preliminary metrics.
- Both analysis endpoints accept a JSON object with a nonempty `address` string.
- Optional manual fields: `price`, `beds`, `baths`, `sqft`, `year_built`,
  `lot_size`, `basement`, `sqft_finished_basement`, `property_type`, `condition`.
- Manual facts override scraped values without mutating the original scrape.
- Browser cleanup runs even when scraping fails.

There is no Perplexity client, database, saved-deal workflow, or authentication in
the current implementation. AI responses are not verified property data. The old
flip formula that inferred resale value from purchase price has been removed.
The investor workspace requires user-supplied resale value, rent, repairs, costs,
and separate financing for each strategy. It does not automatically verify
Connecticut comparable sales, rents, municipal taxes, or closing charges.

Flip results model a constant-balance interest-only purchase loan. Rental results
model a fixed-rate amortizing purchase loan and one stabilized year. Renovation
costs are paid in cash. Neither model includes income taxes or appreciation.
The UI lists these assumptions and exports inputs and results as JSON.

The Load example button uses illustrative assumptions only. No market defaults
are prefilled on initial load.

## Tests

```sh
python -m pytest -q
```

Request tests replace browser and AI services with controlled doubles. They cover
both endpoints, invalid bodies and addresses, provider failures, manual overrides,
and browser cleanup. They do not require API keys, Chrome, or paid API calls.
Live scraping and provider integration require separate verification.

## Files

- `src/deal_calculator.py`: deterministic underwriting and scenario calculations
- `templates/investor.html`: investor comparison interface
- `src/app.py`: Flask routes and manual data merge
- `src/selenium_scraper.py`: property and comparable scraping
- `src/claude_analyzer.py`: prompts, provider calls, evidence-based flip research
- `templates/index.html`: existing analysis interface
- `static/style.css`: styles
- `tests/test_app.py`: offline regressions

## Investor product direction

Start with explicit purchase, renovation, financing, carrying, and exit
assumptions. Calculate results deterministically, show missing information, and
compare downside scenarios. Keep source dates and links with property facts and
comparables. AI commentary should explain the supplied evidence and assumptions.
