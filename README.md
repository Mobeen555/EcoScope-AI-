# EcoScope AI 2.0 — five-agent CrewAI edition

A Streamlit environmental research application with open-data analysis, GIS maps,
charts, citizen observations, exportable reports and **exactly five CrewAI agents**.
This edition preserves the analytical engine and native image handling from the
working 1.1.1 application. It adds a visible **AI team** page and optional AI report
sections. All eight supplied JPG images and the indigo, teal and violet theme are included.

**Upload the complete extracted project. `app.py` alone is no longer sufficient.**

## Pattern and five agents

The selected pattern from your reference picture is **Sequential**. The coordinator
checks the study first, three specialists review their domains, and the reviewer
uses their completed notes to write the final briefing. This keeps the review order
explicit and paces requests to the shared model account.

| Agent definition | Responsibility |
|---|---|
| `agents/coordinator.py` | Study question, coordinates, boundary, dates and evidence coverage |
| `agents/climate_air.py` | Climate, weather, air quality and available river/weather outlooks |
| `agents/geospatial_water.py` | Satellite screening, water proxies, maps' metadata and earthquake records |
| `agents/ecology_field.py` | Biodiversity records and uploaded field measurements |
| `agents/reviewer_reporter.py` | Check specialist notes, identify limitations and write the cited briefing |

There are five real CrewAI `Agent` objects and five tasks. No extra manager or
planning agent is created. All five can share one Groq key and model. The framework
is open source; the hosted model account has its own availability and usage limits.

## Files to upload

| File or folder | Purpose |
|---|---|
| `app.py` | Streamlit interface, images, settings, charts and report controls |
| `environment.py` | Environmental retrieval, scientific calculations, maps and exports |
| `agents/` | Exactly five separate agent definition files |
| `agent_common.py` | Shared constructor settings; does not add another agent |
| `agent_tools.py` | Evidence reading, numeric statistics and quality-check tools |
| `evidence.py` | Scoped evidence snapshots, checks and stale-review detection |
| `crew_workflow.py` | Five tasks, explicit context, citations and execution |
| `crew_runtime.py` | Groq adapter, request budgets and private task-output handling |
| `crew_config.py` | Roles, model default, limits and agent policy |
| `requirements.txt` | Runtime dependency versions, including CrewAI |
| `.streamlit/` | Theme and example secrets configuration |
| `assets/` | All eight original supplied JPGs |
| `examples/` | Blank field-sample CSV template |
| `tests/`, `requirements-dev.txt` | Offline software validation |
| `METHODS.md`, `ARCHITECTURE.md`, `VALIDATION.md` | Scientific methods, design and test limits |
| `.gitignore`, `LICENSE` | Credential exclusions and source-code license |

## Deploy on Streamlit Community Cloud

### 1. Extract the download

Extract `EcoScope_AI_CrewAI_v2.0.zip` and open the `ecoscope_crewai` folder.
The files listed above must remain together. Do not upload the ZIP itself as the app.

### 2. Update your GitHub repository

1. Open your existing EcoScope repository and its application branch.
2. Choose **Add file → Upload files**.
3. Drag the **contents** of `ecoscope_crewai` into the upload area, including
   `agents`, `assets`, `.streamlit`, `examples` and the root Python files.
4. Commit the update. GitHub replaces files with matching paths; you do not need
   to delete the old `app.py` first. Git history retains the previous version.
5. Verify `app.py`, `environment.py`, `crew_workflow.py`, `requirements.txt`,
   `agents/coordinator.py`, `.streamlit/config.toml` and `assets/VvwKz.jpg` exist.
6. Verify the other four agent files and seven images also appear in their folders.

If your file picker hides `.streamlit`, create `.streamlit/config.toml` in GitHub
using **Add file → Create new file** and copy its supplied contents.
Do not commit a real `secrets.toml` or an API key. The `.example` file is safe to upload.

Keep `app.py` at the repository root. If you upload the containing folder too,
the entrypoint becomes `ecoscope_crewai/app.py`; use that path when deploying.

### 3. Configure Streamlit

1. Open https://share.streamlit.io and sign in.
2. For a new deployment, choose **Create app**, select the repository and branch,
   and set **Main file path** to `app.py`.
3. In **Advanced settings**, select **Python 3.12**.
4. For an existing app, confirm its repository, branch and entrypoint are correct.
   A commit triggers a rebuild. Reboot from **Manage app** if needed.

The supplied dependency set was tested on Python 3.12.14. If an existing deployment
uses an incompatible Python version and its settings cannot change it, recreate
the deployment with Python 3.12 using the same repository. Save your app secrets first.

### 4. Enable the five AI agents

Create a Groq key at https://console.groq.com/keys. Add this to Streamlit's
**Secrets** settings, replacing the placeholder:

```toml
GROQ_API_KEY = "YOUR_REAL_GROQ_KEY"
GROQ_MODEL = "openai/gpt-oss-120b"
```

For a new app, Secrets are available under Advanced settings. For an existing
app, open its settings from Manage app. These are **Streamlit secrets**; GitHub
repository secrets are not automatically passed to the running application.

You can instead enter a private key on **AI team** for the current session.
One key serves all five agents. Do not add an OpenAI key merely because the Groq
model ID contains `openai/`. Enter the model ID exactly as provided by Groq.
Check account-supported models if the default is unavailable.

Environmental analysis, maps and standard reports work without any AI key.
The five agents need a working model connection. No separate CrewAI cloud account
is required for this local CrewAI workflow.

### 5. Deploy and check the interface

Click **Deploy**, or wait for the existing app to rebuild. Initial installation
can take several minutes. Confirm that you see **v2.0.0 · CrewAI · 5 agents**, the
**AI team** navigation item and the supplied images. If installation fails, check
the first error in the deployment logs and keep all supplied dependency pins together.

### 6. Run environmental analysis

1. Open **Study & analysis** and search a city or enter coordinates.
2. Enable the optional landmark search for river/lake names. Inspect the returned
   coordinates and boundary; a river name does not define its entire basin.
3. Select historical dates and modules. Start with Climate and Air quality.
4. Click **Run environmental analysis**.
5. Inspect module results, dates, coverage notes and unavailable sources.
6. Add Satellite for actual Sentinel-2 processing. Start with a small boundary,
   one to three months and one to three scenes.

You may draw a polygon or upload WGS84 Polygon/MultiPolygon GeoJSON. Enable the
uploaded/drawn-boundary option to use it. Climate and air values represent model
cells near the centroid; they are not polygon-wide averages. Satellite processing
is bounded to 250 km², six scenes and approximately 600,000 working pixels per scene.

### 7. Run the AI team

1. Open **AI team** using the sidebar or the always-visible button.
2. Supply the key if it is not configured in Secrets.
3. Keep the estimated token budget at or below your account's actual limit.
   The default is a conservative application setting, not a promise of account quota.
4. Enable the checkbox allowing run summaries, coordinates and requested statistics
   to be sent to Groq.
5. Enter a question and click **Run five-agent review**.
6. Wait for all five stages. Pacing can make a review take several minutes.
7. Read the final briefing, expand the five agent notes and inspect request usage.

Example question: “What does this local study support, what remains unavailable,
and which field measurements should we collect next?”

The agents review the **saved analysis** and can read scoped evidence or calculate
statistics from its tables. They do not silently change coordinates, fetch new
satellite data or operate emergency-warning systems. Re-run environmental analysis
to refresh sources. A changed dataset invalidates the previous AI review.

### 8. Add citizen or laboratory observations

Open **Ecology & field**, download the blank CSV, retain its exact column names,
fill your measurements and upload it. Required columns are `site`, `date`,
`latitude` and `longitude`. Optional measurements include `chlorophyll_ug_l`,
`secchi_m`, `total_phosphorus_ug_l`, `dissolved_oxygen_mg_l`, `ph`,
`temperature_c`, `turbidity_ntu` and `notes`. Leave missing measurements blank.

Click **Validate and attach observations**. Out-of-study rows remain in an audit
table and do not enter summaries. Optional Carlson indices apply to suitable
lake/reservoir samples and are calculated separately. Uploaded values are unverified.
Attaching observations clears an old AI review; run the team again to include them.

### 9. Download the report

Open **Reports & sources**. If a current five-agent review completed, you can
include it using the checkbox. Click **Generate report & export package**.

The complete results ZIP includes PDF/HTML reports, Excel, full returned CSV tables,
PNG figures, GeoJSON, metadata and satellite GeoTIFF when available. With AI enabled
it also includes `ai/final_review.md` and `ai/agent_review_and_activity.json`.
The AI interpretation is clearly identified in PDF and HTML. An incomplete or stale
review cannot be included as a completed final review.

PDF and HTML tables are previews; CSV/Excel contain all retrieved rows, subject
to provider retrieval caps. Download before ending the session. There is no
persistent project database in this edition.

## Run locally

Windows PowerShell, inside the extracted `ecoscope_crewai` folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

macOS/Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

For local Secrets, copy `.streamlit/secrets.toml.example` to
`.streamlit/secrets.toml` and enter your key. That real secrets file is excluded
by `.gitignore`. Open the local URL printed by Streamlit.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `ModuleNotFoundError: environment`, `agents` or another project module | Upload all root Python files and the complete agents folder; uploading only app.py is insufficient. |
| Images missing | Upload all eight original JPGs under assets beside app.py. Missing files are named in the UI. |
| Old UI or low-contrast colours | Verify app.py, environment.py and .streamlit/config.toml were all replaced, then reboot. |
| CrewAI dependency error | Use Python 3.12 and the exact supplied requirements; do not combine them with an older requirements file. |
| Groq 401/403 | Check key, model permissions and the Streamlit Secrets location. |
| Groq 400/404 | Check the exact model ID and supported API settings for your account. |
| Groq 429 / token-budget stop | Wait, ask a focused question and check account limits. Other apps sharing the key also consume quota. Partial notes remain available. |
| AI context or request budget reached | Select fewer modules or ask a narrower question. No unbounded automatic retries are performed. |
| A source is unavailable | Read the module error. The app does not replace failed retrievals with example numbers. |
| No water pixels | Check boundary, scene dates and masks. This does not demonstrate clean water or an absent river. |
| Satellite memory/timeout issue | Reduce area and scene count; retain the provided processing limits. |
| Results disappeared after restart | Re-run the analysis; download exports before ending the session. |

## Scope and production use

This is a working research MVP. Rain/weather and river-discharge outlooks come from
the named providers. Earthquakes are observed catalogue events; reliable earthquake
prediction is not implemented. US severe-weather alerts are official alerts where
coverage exists, not a global tornado prediction model. Satellite NDCI is an
uncalibrated screening proxy, not a measured nutrient concentration or confirmed
eutrophication diagnosis. A final AI review is not independent scientific validation.

Open-data endpoints and the Groq account have service terms and quotas. Open-Meteo's
hosted free access is for non-commercial use; data licensing and API access terms
are distinct. Do not assume unlimited free production hosting or inference.

Before a shared policy or operational deployment, add authentication, durable job
and project storage, account-level quotas, provider monitoring and regional
scientific validation. Current pacing is per server process and is not a distributed
quota service. Agents run only after the user's explicit button click.

## Official references

- CrewAI sequential process: https://docs.crewai.com/en/learn/sequential-process
- CrewAI custom LLM: https://docs.crewai.com/en/learn/custom-llm
- Streamlit deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Streamlit secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Groq API and limits: https://console.groq.com/docs/api-reference and https://console.groq.com/docs/rate-limits
- Open-Meteo access: https://open-meteo.com/en/pricing

See METHODS.md, ARCHITECTURE.md and VALIDATION.md for implementation and validation details.
