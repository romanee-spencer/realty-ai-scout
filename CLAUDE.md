# Realty AI Scout development notes

Read README.md for current behavior and setup. Run `python -m pytest -q` before
submitting changes. Tests must remain offline and must not start browsers or paid
provider calls.

The current components are src/app.py, src/selenium_scraper.py,
src/claude_analyzer.py, templates/index.html, and static/style.css. There is no
Perplexity client or data consolidator module.

For investor features, use deterministic calculations with explicit assumptions.
Do not infer resale value from purchase price or substitute fixed placeholder
values for missing market data. Keep source evidence distinct from AI commentary.
