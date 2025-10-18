# Project Empathy

Project Empathy is a production-ready yet lightweight data pipeline that collects, cleans, translates, analyzes, and exports Malaysian news coverage related to bullying, suicide, and homicide among students. The toolkit is designed with an ethics-by-design approach, respecting source terms of use and emphasizing transparent citations.

## Features

* Automated discovery of credible Malaysian outlets across English, Malay, and Chinese languages.
* Best-effort crawling and NewsAPI integration for article collection with rate-limiting.
* Data cleaning, boilerplate removal, and translation to English (Malay/Chinese to English via Google Translate).
* NLP pipeline covering TF-IDF keyword frequency, category co-occurrence, and TextBlob sentiment.
* SQLite-backed storage with structured models and parquet/CSV exports for Power BI.
* Typer-based CLI orchestration with modular steps (`pe crawl`, `pe clean`, `pe translate`, etc.).
* HTML report summarizing activity and key metrics.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m textblob.download_corpora  # first-run setup for sentiment analysis
```

Alternatively you can install in editable mode:

```bash
pip install -e .
```

## Quick Start

1. Initialize configuration and environment templates:

   ```bash
   pe init
   ```

2. Edit the generated `.env` and `config.yaml` to suit your needs. Supply `NEWSAPI_KEY` if available.
3. Run the pipeline:

   ```bash
   pe all
   ```

   Individual steps are also available: `pe crawl`, `pe clean`, `pe translate`, `pe analyze`, `pe export`.

## Configuration

Configuration is YAML-based and validated with Pydantic. See `config.example.yaml` for the full schema. Key sections include:

* `storage`: Database and data directory settings
* `news`: Domains, languages, keywords, and request pacing
* `pipeline`: Thresholds and toggles for cleaning, translation, and analysis

Environment variables live in `.env` (see `.env.example`). Only `NEWSAPI_KEY` is required for NewsAPI integration; the rest of the pipeline functions without it.

## Data Ethics

* Robots.txt is honored via pre-flight checks and domain allow-listing.
* Rate-limiting (requests per minute) and retry logic mitigate traffic bursts.
* Personally identifiable information (PII) is not extracted. Content is used for aggregate insights only.
* Every exported article contains citation metadata: source, URL, and publication date.

## Outputs

* `data/empathy.db`: SQLite database storing raw, clean, and analyzed article tables.
* `data/*.parquet`: Intermediate storage for clean datasets.
* `outputs/`: Final CSVs and HTML report for Power BI consumption.

## Development

Run the test suite with:

```bash
pytest
```

The codebase uses type hints and logging extensively. New modules should follow the patterns demonstrated in the existing implementation. Contributions should include appropriate unit tests and documentation.

## License

This project is released under the MIT License. See `LICENSE` for details.
