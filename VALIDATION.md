# EcoScope AI 2.0 — validation record

Checked on 28 September 2026 using Python 3.12.14, CrewAI 1.15.22 and the supplied
dependency pins. These are software checks, not evidence of environmental
measurement accuracy or operational forecasting skill.

## Automated checks

**32 tests pass:** 17 core checks and 15 CrewAI/interface/export checks.
The installed dependency set also passes `uv pip check`.

Core checks cover study geometry, dates and area limits; spectral-index missing
data; scale/offset and nodata handling; partial-month precipitation; field units
and sample filtering; individual Carlson indices; independent provider failures;
restricted numerical tools; and spreadsheet formula escaping.

CrewAI checks cover:

- Exactly five definition files, five actual agents and five tasks; no implicit manager.
- The real CrewAI sequential executor with controlled Groq HTTP responses,
  including actual quality-check and numeric-statistics tool calls.
- A provider 429 after one completed stage: partial notes retained and later HTTP
  requests stopped; provider response bodies are not displayed.
- Credential separation between adapter instances and exclusion from serialization.
- Clean role/content messages without unsupported cache metadata.
- Request budget, oversized request and truncated model-output handling.
- Specialist scope restrictions, invalid sums and missing values remaining unavailable.
- No-water, low-coverage, inconclusive change and partial-month quality checks.
- Rejection of unknown citation IDs and uncited final output when sources exist.
- Data mutation invalidating a completed AI review before report generation.
- Escaped AI content in HTML, generated PDF, and complete ZIP/GIS entries.
- All eight Streamlit pages opening without exceptions and visible AI setup.
- The actual Streamlit AI button through all five stages and into an AI-inclusive
  report, with controlled model responses. Progress callbacks use a queue so only
  the Streamlit script thread updates the UI.

Run locally from the project folder:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

The tests' synthetic values are clearly labelled QA fixtures. The application
never substitutes those fixtures for failed environmental retrievals.

## Additional checks

- A context-size check using previously retrieved module data and controlled
  agent notes completed all five stages. Eight model requests were exercised;
  estimated prompt plus reserved-output sizes ranged from 3,326 to 4,826 tokens,
  below the configured 6,000-token pacing budget. This is an estimate for that
  check, not a guarantee for every question, model or dataset.
- All supplied Python files compile. The eight image assets are preserved
  byte-for-byte from the working image-fixed package.
- A QA PDF containing the new five-agent narrative was rendered. The narrative
  and following map page were visually checked for legibility and clipping.

## Baseline retrieval checks retained

This version preserves the working environmental adapters from 1.1.1. Earlier
checks successfully exercised Open-Meteo ERA5, seven-day weather, five-day air
quality, river discharge, USGS, GBIF, city and landmark geocoding, US NWS alerts,
and Earth Search Sentinel-2 Collection 1 COG processing. These historical checks
do not establish current provider uptime or validate every location.

The earlier satellite test processed actual scene
`S2B_T43SCT_20250529T055506_L2A` near Rawal Lake, with STAC scale/offset metadata,
SCL masking and index generation. This was a software reproducibility check,
not a present-day water-quality assessment. The app retains acquisition and
retrieval dates in source records and never promotes a QA fixture to live data.

## Remaining limits

- No real Groq key was supplied. A live model-to-provider run was **not** tested.
  Model wording, real account quotas and tool-use choices require a first live
  run after the user adds a key. Controlled tests exercise the actual framework
  and tools while mocking only the external model's HTTP responses.
- No deployment was made to the owner's GitHub or Streamlit account. AppTest
  checks application behaviour; a deployed-browser layout/load review remains.
- No comparison with laboratory samples, river gauges or station observations
  was performed. There is no validated local flood or water-quality model.
- No multi-user load or distributed quota testing was performed. This edition
  has no durable job recovery, saved project database or continuous monitoring.
- Citation checks validate known IDs and formatting, not every scientific claim.
  Agent agreement is not independent scientific validation.
- CrewAI emits deprecation notices and a callback-serialization warning under
  this pinned version. Persistent workflow checkpoints are intentionally unused.
  Review the compatibility tests before upgrading the framework.

See README.md for deployment, METHODS.md for scientific scope and
ARCHITECTURE.md for execution and privacy behaviour.
