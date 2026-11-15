# Data Requests Log

Road transport energy demand in rural area: Gorbeialdea case study.

This document tracks every dataset that must be requested from third parties, why it is needed, and the status of each request. Datasets that are openly downloadable are listed separately at the end. Keep this file up to date after every contact; the Git history then serves as the audit trail.

- **Created:** 2026-11-15

## 1. Status legend

| Status | Meaning |
|---|---|
| `NOTSENT` | Request not yet sent |
| `SENT` | Request sent, awaiting reply |
| `CHASED` | Reminder sent |
| `PARTIAL` | Some of the data received |
| `RECEIVED` | Data received and stored |
| `DENIED` | Request refused (record the reason) |
| `FALLBACK` | Fallback source adopted instead |


## 2. Tracking summary

| ID | Dataset | Recipient | Status | Sent | Reply | Notes |
|---|---|---|---|---|---|---|
| R01 | Hourly traffic counts by vehicle type | Diputación Foral de Álava (roads / mobility) | NOTSENT | | | |
| R02 | Cordon counts and plate/device sampling | Diputación Foral de Álava; own sampling | NOTSENT | | | |
| R03 | Bus occupancy per segment and hour | Bus operator | NOTSENT | | | |
| R04 | Complete GTFS, including shift and vehicle data | Bus operator / Basque Government | NOTSENT | | | |
| R05 | Vehicle fleet by municipality, fuel, type and age | DGT / Eustat | NOTSENT | | | |
| R06 | Odometer readings from vehicle inspections (ITV) | ITV operator / Basque Government | NOTSENT | | | |
| R07 | Regional LiDAR elevation data | Basque Government (Geoeuskadi) | NOTSENT | | | |
| R08 | Mobility survey microdata | Basque Government | NOTSENT | | | |
| R09 | Electricity grid capacity and charging points | Distribution system operator / Basque Government | NOTSENT | | | |
| R10 | Competence and speed-limit records per road segment | Diputación Foral de Álava / Basque Government | NOTSENT | | | |

## 3. Detailed requests

Each request below should be adapted into a formal letter or e-mail. Replace the bracketed placeholders before sending.

### R01. Hourly traffic counts by vehicle type

- **Recipient:** Diputación Foral de Álava, department responsible for roads and traffic counting stations (exact unit to be confirmed).
- **Needed for:** M2 (flow model, training and validation of the graph neural network), M6 (speed management).
- **Data requested:**
  - Hourly intensity (vehicles per hour) for every permanent and temporary counting station located in or around the study area.
  - Breakdown by vehicle class, at minimum light and heavy vehicles; buses if available.
  - Average speed per station and hour, and speed percentiles if recorded.
  - Station coordinates, road identifier, kilometre point and direction of travel.
  - A full year of data for the base year, so that all day types (school weekday, non-school weekday, Saturday, Sunday or holiday) and seasons are covered.
- **Preferred format:** CSV or Excel, one row per station, hour and direction.
- **Fallback:** published annual average daily traffic (AADT) maps and yearbooks; use typical days with wider uncertainty intervals.
- **Justification:** open research on rural energy demand; results will be shared with the administration.

### R02. Cordon counts and plate or device sampling

- **Recipient:** Diputación Foral de Álava and, if needed, the Basque Government traffic authority. For sampling, the study team itself.
- **Needed for:** M2 (calibration of the through-traffic share and of the trip-type attribution), the preliminary through-traffic estimate.
- **Data requested:**
  - Hourly counts at every entry and exit road of the study area (the cordon), by direction and vehicle class.
  - Any existing origin-destination survey, licence-plate survey or Bluetooth/Wi-Fi sampling for the area.
  - Authorization to carry out a short plate or device sampling campaign at the main road entry and exit points, if none exists.
- **Data-protection note:** any plate or device sampling involves personal data. Plan pseudonymization at source (hashed identifiers with a rotating salt, no storage of raw plates), a legal basis, and, where required, a data protection impact assessment before fieldwork. Consult the institution's data protection officer.
- **Fallback:** infer the cordon from station counts on the main road plus origin-destination matrices from mobile-phone data; document the resulting uncertainty.

### R03. Bus occupancy per segment and hour

- **Recipient:** Operator of the bus lines serving the study area (to be identified from the GTFS feed).
- **Needed for:** M1 (bus mass depends on occupancy), M3 (mode choice), M4 (frequency optimization and occupancy threshold).
- **Data requested:**
  - Passenger boardings and alightings per stop, trip and date, or passenger load per segment, from ticketing or automatic passenger counters.
  - Coverage of the base year, with line, direction, scheduled time and vehicle type.
  - Vehicle fleet used per line (size, fuel, mass, seating capacity) and empty (deadhead) kilometres.
  - Fare structure and ticket types.
- **Preferred format:** CSV with one row per trip and stop.
- **Fallback:** manual sampling on selected lines, then scenario ranges for occupancy and a sensitivity analysis.
- **Risk:** this is the largest data risk of the project. Ask for it first.

### R04. Complete GTFS

- **Recipient:** Bus operator, or the Basque Government transport authority.
- **Needed for:** M1 (buses per segment and hour via map-matching), M4.
- **Data requested:**
  - The latest GTFS feed for all lines serving the study area, including `shapes.txt` and `calendar_dates.txt`.
  - Confirmation that the public feeds (Open Data Euskadi and the national access point, NAP) are complete; request missing lines, on-demand services and school transport.
- **Fallback:** public GTFS feeds; reconstruct missing shapes by routing between stops.

### R05. Vehicle fleet by municipality

- **Recipient:** DGT (Dirección General de Tráfico) and Eustat.
- **Needed for:** M5 (fuel substitution) and the resident consumption indicator.
- **Data requested:**
  - Vehicles registered per municipality of the study area, by vehicle type, fuel, engine size or power category, emission standard and registration year.
  - The same series for at least the last five years, to estimate fleet renewal rates.
- **Preferred format:** CSV or Excel at the finest territorial level available.
- **Fallback:** the public DGT fleet statistics at municipal level; scale by population if finer data are unavailable.

### R06. Odometer readings from vehicle inspections (ITV)

- **Recipient:** ITV operator in Álava and the competent Basque Government department.
- **Needed for:** annual kilometres per vehicle, which improves the resident consumption indicator.
- **Data requested:** anonymized odometer readings with inspection date, vehicle type, fuel and registration municipality.
- **Data-protection note:** request only anonymized or aggregated records; no plate numbers or owner data.
- **Fallback:** mobility surveys and national average annual mileage by vehicle type; **do not** use fuel sales as a proxy (they are dominated by through traffic).

### R07. Regional LiDAR elevation data

- **Recipient:** Basque Government, Geoeuskadi infrastructure.
- **Needed for:** M1 (accurate slopes, especially on short segments).
- **Data requested:** the highest-resolution digital terrain model available for the study area and its surroundings, with the licence terms.
- **Fallback:** Copernicus DEM (30 m), with stronger smoothing and a documented slope error.

### R08. Mobility survey microdata

- **Recipient:** Basque Government (mobility survey unit) and Eustat.
- **Needed for:** calibration of the logit model in M3 and the route-choice behaviour in M6, and the value of time.
- **Data requested:** anonymized microdata or tabulations for the study area by trip purpose, mode, duration, distance, time of day and household car availability.
- **Fallback:** published aggregate results and literature values for the value of time, with sensitivity analysis; plan a short local stated-preference survey.

### R09. Electricity grid capacity and charging points

- **Recipient:** Local distribution system operator and the Basque Government energy department.
- **Needed for:** M5 (feasibility of electrification in dispersed settlements).
- **Data requested:** location and power of existing public charging points; available capacity or constraints at substations serving the study area; planned deployments.
- **Fallback:** public charging-point registries and national mix projections.

### R10. Road competence and speed-limit records

- **Recipient:** Diputación Foral de Álava and the Basque Government.
- **Needed for:** M6 (which administration controls each segment, and the current legal speed limits).
- **Data requested:** road inventory with administrative owner, legal speed limit and road class per segment.
- **Fallback:** OpenStreetMap `maxspeed` tags, verified by field checks on the main corridors.

## 4. Open data (no request needed)
 
These sources can be downloaded directly. Record the exact version, access date and licence in `data/README.md` when each is downloaded.
 
| Dataset | Source | Access date | Licence | Status |
|---|---|---|---|---|
| Road network | OpenStreetMap (via `osmnx`) | | ODbL | NOTSENT |
| Digital elevation model, 30 m | Copernicus DEM / SRTM | | Check provider | NOTSENT |
| Public transport timetables | Open Data Euskadi, national access point (NAP) | | Check provider | NOTSENT |
| Origin-destination matrices | Ministry of Transport (MITMA) open mobility data | | Check provider | NOTSENT |
| Population and employment | INE, Eustat | | Check provider | NOTSENT |
| Municipal and concejo boundaries | Geoeuskadi, IGN | | Check provider | NOTSENT |
| Emission and consumption factors | COPERT, HBEFA (confirm licence terms) | | Check provider | NOTSENT |

## 5. Legal basis for the requests

Public-sector data requests can reference the following frameworks. Confirm the current text and the correct instrument with the institution before citing them.

- **Transparency and access to public information:** Law 19/2013 (national) and the corresponding Basque regulation.
- **Re-use of public-sector information:** Law 37/2007, which transposes the EU open data framework.
- **Access to environmental information:** Law 27/2006, which may apply to traffic and emissions data.
- **Personal data:** Regulation (EU) 2016/679 (GDPR) and Organic Law 3/2018, relevant to R02 and R06.

## 6. Request template

Adapt this text for each recipient.

```
Subject: Request for [dataset] for a research study on rural road transport energy demand

Dear [Name / Department],

I am writing to request access to [dataset, period, and territorial scope]
for a research study on the energy demand of road transport in the Cuadrilla
de Gorbeialdea (Álava). The study builds an open, reproducible model of
hourly energy consumption on the road network, and evaluates measures such
as public transport redesign, fuel substitution and speed management.

Specifically, I would be grateful to receive:
  - [bullet list of fields, period, format]

The data will be used only for research purposes, [anonymized / aggregated as
required], and the results will be shared with [institution] and published
openly. I am happy to sign a data-use agreement and to discuss any
restrictions that apply.

Please let me know if you need further information or if another unit is
better placed to handle this request.

Kind regards,
[Name]
[Affiliation / contact details]
```

## 7. Correspondence log

Add one line per contact, newest last.

| Date | Request ID | Contact (name, unit, e-mail) | Channel | Summary | Next action | Due |
|---|---|---|---|---|---|---|
| | | | | | | |

## 8. Immediate actions

1. Identify the bus operator and the correct unit at the Diputación Foral de Álava (R01, R02, R03).
2. Send R01, R02 and R03 first; they gate the flow model and the bus energy model.
3. Send R04 and R05 in the same week.
4. Download all open data in Section 4 and log it in `data/README.md`.
5. Review this file after two weeks and chase any request still marked `SENT`.