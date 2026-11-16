# Agents: Project Context and Operating Rules

This document describes the repository, its automation, its conventions and the rules an AI assistant must follow when working in it. It is written to be pasted as a system prompt or stored as a workspace instruction file.

## 1. Purpose of the project

The repository supports a scientific study on **road transport energy demand in rural areas**, with the **Cuadrilla de Gorbeialdea (Álava, Basque Country, Spain)** as the case study. It builds a digital energy model of regional mobility from open data and answers six chained research questions:

| ID | Question | Models |
|---|---|---|
| Q1 | What is the actual energy demand profile of road transport, by segment and hour, broken down by trip origin (residents, inbound and outbound trips, through traffic)? | M1, M2 |
| Q2 | Which technical, operational and demand-management levers can reduce or replace fossil fuel consumption? | M7 |
| Q3 | What net energy saving results from shifting travellers from private vehicles to public transport by redesigning the service? | M3, M4 |
| Q4 | What reduction in petroleum products results from fuel substitution, given the regional fleet composition? | M5 |
| Q5 | How much energy does lowering speed limits save, and what travel-time penalty does it cause? | M6 |
| Q6 | Which combination of the solutions from Q3, Q4 and Q5 maximizes savings and decarbonization at the lowest economic and social cost? | M7 |

Central hypothesis: rural transport energy consumption is concentrated in few segments, time slots and vehicle types, and the effect of a measure depends on where it is applied and who generates the trip. No single lever solves the problem, and savings from different levers overlap and are not additive.

The full methodology is in `methodology.md`.

## 2. Environment

- **Operating system:** Windows. Commands are written for PowerShell.
- **Editor:** Visual Studio Code.
- **Languages:** Markdown for writing, Python for code.
- **Version control:** Git, hosted on GitHub.
- **Repository:** `https://github.com/aritz-ezkerro/rural-mobility-energy-model.git`
- **Local folder:** `C:\Users\Public\Documentos\aritz-ezkerro\rural-mobility-energy-model`
- **Branch:** work happens directly on `main`, because the automation triggers on pushes to `main`.
- **Cost model:** zero-cost and subscription-free. Use only free tools and open data.

The repository name is `rural-mobility-energy-model`. The Python package is named `gorbeialdea` and lives in `src/gorbeialdea/`.

## 3. Language and style rules

1. All manuscript text, code, comments, documentation and commit messages must be in **clear, formal academic and technical English**.
2. The manuscript is Markdown. **Do not use LaTeX document commands** (`\label`, `\ref`, `\eqref`, `\begin{equation}`, `\usepackage`), because nothing is compiled with LaTeX.
3. Equations use GitHub-compatible math: inline `$...$` and display `$$...$$`. Number display equations manually with `\tag{n}` and refer to them as "Equation (n)". Keep a display equation outside list items to avoid rendering problems on GitHub. Do not place a `|` character inside a Markdown table cell that contains math.
4. Write CO₂ with the subscript character. Use en dashes for numeric ranges.
5. Files must render correctly on GitHub and in the Visual Studio Code Markdown preview.

## 4. Repository structure

```
rural-mobility-energy-model/
├── methodology.md        Human-authored study methodology (primary manuscript)
├── log.md                AUTO-GENERATED work log. Never edit.
├── generate_log.py       Rebuilds log.md from the Git history
├── README.md             Project overview, setup, workflow, commit convention
├── .gitignore
├── requirements.txt      Core Python dependencies (unpinned at the start)
├── pyproject.toml        Package metadata (setuptools, src layout)
├── .vscode/settings.json Editor settings (UTF-8, LF, Markdown, Python interpreter)
├── .github/workflows/build.yml   Continuous integration
├── config/study.yaml     Single source of truth for study parameters
├── data/
│   ├── README.md         Dataset register and data policy
│   ├── raw/              Original downloads. Gitignored. Never modified.
│   ├── interim/          Intermediate files. Gitignored.
│   └── processed/        Small final tables. Versioned only if small.
├── src/gorbeialdea/
│   ├── common/               Config loader, units, energy factors
│   ├── m1_energy_graph/      M1
│   ├── m2_flow/              M2
│   ├── m3_modal_shift/       M3
│   ├── m4_service_opt/       M4
│   ├── m5_fuel_substitution/ M5
│   ├── m6_speed/             M6
│   └── m7_integration/       M7
├── scripts/              Numbered entry points (01_..., 02_...)
├── notebooks/            Exploration only; never the source of reported results
├── tests/                Unit tests (physics, flow conservation, units)
├── results/              Generated tables and data files
├── figures/              Generated figures
└── docs/
    ├── data_requests.md  Log of third-party data requests
    └── decisions.md      Assumptions and design decisions
```

Design principles:

- **One Python module per model (M1 to M7), one manuscript section per research question.**
- **Every number reported in the manuscript must be generated by code** into `results/` or `figures/`. Never type results by hand.
- **No magic numbers in code.** Parameters come from `config/study.yaml`.
- **Raw data stays out of Git.** Reproducibility comes from the dataset register in `data/README.md` plus download scripts, not from stored files.
- Folders that must exist but would be empty contain a `.gitkeep` file.

## 5. Automation

### 5.1 Work log generation

`generate_log.py` regenerates `log.md` completely on every run. It:

1. Reads the full Git history (`git log --reverse --no-merges`).
2. Converts commit timestamps to the **Europe/Madrid** timezone (requires the `tzdata` package on Windows).
3. Parses the subject line for the session start time (see Section 6).
4. Writes one entry per work session, in chronological order, with title, start, end, duration and bullet points.
5. Skips commits made by `github-actions[bot]` and commits whose subject starts with `[skip ci]` or `Update work log`.
6. Records commits without a bracketed start time with "Start: not recorded".

`log.md` entry format:

```
## 2026-11-15 · Session title

**Start:** 2026-11-15 09:00 · **End:** 2026-11-15 17:21 · **Duration:** 8 h 21 min

- First task
- Second task
```

Commit messages may use inline Markdown such as `code`. The script performs no escaping.

### 5.2 GitHub Actions workflow

File: `.github/workflows/build.yml`, name "Update work log". It runs on every push to `main`:

1. Skips the job when the actor is `github-actions[bot]`, so an infinite loop cannot occur.
2. Checks out the repository with `fetch-depth: 0` so the full history is available.
3. Sets up Python 3.12 and runs `python generate_log.py`.
4. Stages `log.md`. If it changed (this also detects a newly created file), commits it as `github-actions[bot]` with the message `[skip ci] Update work log`, runs `git pull --rebase origin main` and pushes.

The workflow has `permissions: contents: write`. The repository setting **Settings → Actions → General → Workflow permissions** must be "Read and write permissions".

The workflow does not compile anything. A PDF build (for example with Pandoc) may be added later if needed.

### 5.3 Local working cycle

1. `git pull` before starting, to receive the `log.md` updated by the bot.
2. Edit and preview locally (`Ctrl+Shift+V` for the Markdown preview).
3. Commit and sync at the end of the session.

## 6. Commit message convention

The log depends on it, so every commit message must follow it exactly:

```
[HH:MM] Concise English title of the session

- First task completed
- Second task completed
```

- The session **end** is the commit timestamp.
- `[HH:MM]` is the session **start** (same-day session). For multi-day sessions use `[YYYY-MM-DD--HH:MM]`.
- Body lines beginning with a hyphen and a space become bullet points.
- When asked to summarize a session or suggest a commit message, produce text in exactly this format so it can be pasted into the Source Control panel. Use `HH:MM` as a placeholder if the start time is unknown, and say so.

## 7. Configuration file

`config/study.yaml` contains, in this order:

- `study`: title, case study, timezone, geographic CRS (EPSG:4326), projected CRS (EPSG:25830), base year, municipalities, influence area buffer.
- `day_types`: school weekday, non-school weekday, Saturday, Sunday or public holiday, each with `n_days` (must sum to the days of the base year); optional seasons.
- `vehicle_classes`: car, van, truck, bus.
- `trip_types`: internal, outbound_resident, inbound_nonresident, through.
- `solution_scope`: which trip types each solution can act on.
- `fuels`: diesel, petrol, electricity, HVO, biomethane, hydrogen, each with unit, net calorific value, petroleum fraction and primary energy factor.
- `physics`: gravity, air density, slope smoothing.
- `vehicle_parameters`: mass, rolling resistance, CdA and drivetrain efficiency per class.
- `public_transport`, `speed_management`, `optimization`, `sensitivity`, `random_seed`.

Convention: `null` means "not decided yet". Values marked `TO_CONFIRM` must be resolved, with their source recorded, before the pipeline is run. Values marked "provisional" (for example the calorific values of diesel and petrol) must be verified against an official source. **Never invent a value to fill a `null`.** Ask the user or leave it unresolved.

## 8. Modelling architecture

### 8.1 Concepts

- **Unit of analysis:** road segment × hour × day type. Annual result = sum over day types of (number of days × daily result).
- **Territorial consumption** (Equation 1): energy spent on the region's roads by all vehicles. **Resident consumption** (Equation 2): energy of the residents' trips, including segments outside the region.
- **Trip types:** internal, outbound resident, inbound non-resident, through. Each flow is labelled by who generates it, and each measure is applied only to the part it can act on.
- **Share of through traffic:** `E_terr^through / E_terr`. It sets the ceiling of local measures and must always be reported.
- **Sign convention:** ΔE < 0 means saving; ΔE > 0 means increased consumption.
- **Energy basis:** primary energy, with one conversion factor per carrier.

### 8.2 What each solution acts on

| Solution | Acts on | Notes |
|---|---|---|
| Q3, public transport | Internal, outbound resident and inbound non-resident trips | Complete trip counted, including the part outside the region. Report within-region and complete-trip savings separately. |
| Q4, fuel substitution | Vehicles of residents (internal and outbound), wherever they go | Through traffic and non-residents are out of reach. |
| Q5, speeds | All traffic on affected segments, including through traffic | Competence often belongs to another administration. |

### 8.3 Models

| Model | Input | Output | Answers |
|---|---|---|---|
| M1 Energy graph | OSM, DEM, GTFS | Directed graph with slope and specific consumption per segment and vehicle, from a longitudinal dynamics model (Equation 3) | Q1 |
| M2 Flow and attribution | Counts, cordon counts, OD matrices, road variables | Hourly flow with uncertainty on the whole network, split by trip origin | Q1 |
| M3 Modal shift | Times, costs, surveys | Cars removed per segment and hour for each frequency level (logit model) | Q3 |
| M4 Service optimization | M1 to M3 plus constraints | Optimal frequencies and fleet scenarios; net energy (Equation 4) | Q3 |
| M5 Fuel substitution | Resident fleet, technologies, electricity mix | Petroleum consumption per penetration scenario (Equation 5) | Q4 |
| M6 Speed and segments | M1, M2, new speeds, route-change model | Saving, traffic diversion and time penalty per segment | Q5 |
| M7 Integration | Results of M1 to M6 and costs | Lever ranking, Pareto frontier, sensitivity and uncertainty | Q2, Q6 |

### 8.4 Methodological commitments the assistant must respect

- Model the road network as a **directed graph** (each direction is a distinct edge), with slope from a digital elevation model.
- Always compare the graph neural network with simple baselines (pure OD assignment, gradient boosting). If the network does not outperform them, state it.
- Use **spatial cross-validation** (hold out entire stations or zones), not random splits.
- Report **intervals and ranges, never single figures**. Use global sensitivity analysis (Sobol or Morris) and Monte Carlo propagation.
- Impose a **minimum service coverage** in the bus optimization; otherwise the energy optimum cuts service.
- Include **induced demand, rebound effect and traffic diversion** to secondary roads.
- Evaluate measure combinations with the complete model, not as a sum of individual savings.
- Present results as a **Pareto frontier**, not a single optimum.
- **Do not use fuel sales** as a proxy for resident consumption: a main road makes local stations serve through traffic.
- Handle the circularity occupancy → mass → consumption → decision iteratively.

## 9. Data management

- `docs/data_requests.md` tracks requests to third parties (R01 to R10: traffic counts, cordon counts, bus occupancy, GTFS, vehicle fleet, ITV odometer readings, LiDAR, mobility surveys, grid and charging data, road competence). It contains a status legend, a tracking table, a detailed entry per request with a fallback, an open data table, the legal frameworks, an e-mail template and a correspondence log.
- Status values: `NOTSENT`, `SENT`, `CHASED`, `PARTIAL`, `RECEIVED`, `DENIED`, `FALLBACK`.
- `data/README.md` is the **dataset register**: provider, version or period, access date, licence, URL or request ID, local path. A dataset must have a row before it is used.
- Never edit `data/raw/`. Cleaning is done by scripts writing to `data/interim/` or `data/processed/`.
- Data received under a restricted agreement must not be committed.
- Plate or device sampling and ITV records involve personal data: require pseudonymization or aggregation and a data protection assessment before fieldwork.

Main data risk: availability of real bus occupancy and of traffic counts on secondary roads and at the cordon.

## 10. Python environment

- Python 3.10 or later, virtual environment in `.venv/` (gitignored), activated with `.venv\Scripts\Activate.ps1`.
- Install with `pip install -r requirements.txt` and `pip install -e .`.
- Core packages: numpy, pandas, scipy, pyyaml, matplotlib, tzdata, osmnx, geopandas, rasterio, networkx, gtfs-kit, scikit-learn, biogeme, pyomo, highspy, pymoo, SALib, pytest.
- `torch` and `torch_geometric` are **not** in `requirements.txt`; they are installed when M2 starts, following their official instructions.
- After M1 works, record the exact environment with `pip freeze > requirements.lock.txt`.

## 11. Mandatory operating rules for the assistant

1. **Never edit `log.md` directly.** It is overwritten by the workflow. To change its layout or parsing, modify `generate_log.py`.
2. **Never commit raw or interim data**, and never add a file under `data/raw/` to Git.
3. **Do not invent data, parameters, contacts, citations or legal references.** Leave `null` and flag the gap. State clearly when something could not be verified or tested.
4. **Do not hard-code parameters.** Read them from `config/study.yaml`.
5. **Do not type results by hand** into the manuscript; generate them from code.
6. **Keep the commit convention** (Section 6) in every suggested commit message.
7. **Do not add LaTeX** or LaTeX-based tooling.
8. **Work on `main`.** Do not propose feature branches unless the user asks, because they complicate the automated log.
9. Keep notebooks for exploration only.
10. When in doubt about a decision that affects the study design (zone, base year, thresholds, weights), ask the user and record the decision in `docs/decisions.md`.

## 12. Current status

The repository is in the **scaffold and design phase**:

- Done: folder structure, `methodology.md`, work log automation, `config/study.yaml` (with unresolved values), `docs/data_requests.md`, README files, dependency files.
- Not yet implemented: all code under `src/gorbeialdea/`, the configuration loader, scripts, tests, `docs/decisions.md` content, and any data download.
- Pending decisions: study area (municipalities and influence buffer), base year, day-type weights, vehicle parameters, primary energy factors, minimum coverage, critical travel-time penalty.
- Immediate next steps: send the data requests (R01 to R03 first), implement the configuration loader in `src/gorbeialdea/common/`, then build M1 (directed OSM graph, DEM slopes, longitudinal dynamics model, validation against COPERT/HBEFA), and a preliminary estimate of the through-traffic share.