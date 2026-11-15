# Data Documentation

This file records the provenance of every dataset used in the study. It makes the analysis reproducible without storing raw data in Git.

## Folder policy

| Folder | Contents | In Git? |
|---|---|---|
| `data/raw/` | Original downloads and received files, never modified | No (gitignored) |
| `data/interim/` | Intermediate files produced by scripts | No (gitignored) |
| `data/processed/` | Small final tables used by the models | Yes, only if small |

Rules:

1. Never edit files in `data/raw/`. All cleaning is done by scripts that write to `data/interim/` or `data/processed/`.
2. Every dataset must have a row in the table below before it is used.
3. Third-party data received under a restricted agreement must not be committed. Record only its description here.
4. Request status and correspondence are tracked in `docs/data_requests.md`.

## Dataset register

| Dataset | Provider | Version or period | Access date | Licence | URL or request ID | Local path | Notes |
|---|---|---|---|---|---|---|---|
| Road network | OpenStreetMap | | | ODbL | | `data/raw/osm/` | |
| Digital elevation model | Copernicus DEM | | | | | `data/raw/dem/` | |
| Public transport timetables (GTFS) | Open Data Euskadi, NAP | | | | | `data/raw/gtfs/` | |
| Origin-destination matrices | MITMA | | | | | `data/raw/od/` | |
| Population and employment | INE, Eustat | | | | | `data/raw/socio/` | |
| Municipal boundaries | Geoeuskadi, IGN | | | | | `data/raw/boundaries/` | |
| Emission and consumption factors | COPERT, HBEFA | | | | | `data/raw/factors/` | Check licence terms |
| Traffic counts | Diputación Foral de Álava | | | | R01 | `data/raw/counts/` | |
| Cordon counts | Diputación Foral de Álava | | | | R02 | `data/raw/cordon/` | |
| Bus occupancy | Bus operator | | | | R03 | `data/raw/occupancy/` | |
| Vehicle fleet | DGT, Eustat | | | | R05 | `data/raw/fleet/` | |

## Retrieval

Download scripts will live in `scripts/` with numbered names, so that any dataset that can be fetched automatically is retrieved by code rather than by hand. For files that must be requested or downloaded manually, describe the steps here.