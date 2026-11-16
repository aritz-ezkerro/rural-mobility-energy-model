**STUDY DESIGN REPORT — CASE STUDY: CUADRILLA DE GORBEIALDEA (ÁLAVA)**

# Road transport energy demand in rural areas: diagnosis, levers and optimal strategy

The chronological record of work sessions is in [log.md](log.md) (auto-generated).

---

## 1. Approach and research questions

In rural and mountain areas such as Gorbeialdea, transport is one of the main sources of energy consumption and emissions, and it depends almost entirely on the private car and on petroleum products. The study builds a **digital energy model of the regional mobility system**, using open data, to answer six chained questions.

- **Q1.** What is the **actual energy demand profile** of road transport in the region, spatially disaggregated (segment by segment) and temporally disaggregated (hour by hour), and **broken down by trip origin** (residents, inbound and outbound trips, and through traffic)?
- **Q2.** Which **technical, operational and demand-management levers** can be applied to reduce or replace the fossil fuel consumption identified?
- **Q3.** What **net energy saving** can be achieved by shifting travellers from the private vehicle to public transport by redesigning the service supply?
- **Q4.** What **reduction in petroleum product consumption** is achieved by replacing fossil fuels with alternative energy carriers, given the composition of the regional vehicle fleet?
- **Q5.** To what extent does the **operational management of the road network**, especially lowering maximum speeds, reduce energy consumption without causing critical travel-time penalties?
- **Q6.** Which **combination of the solutions from Q3, Q4 and Q5** maximizes energy savings and decarbonization at the lowest economic and social cost for the region?

**How they fit together.** Q1 is the diagnosis and sets the **baseline**. Q2 is the catalogue of levers and their screening. Q3, Q4 and Q5 assess the three main solutions (public transport, petroleum substitution and network management) against that baseline, each on the share of consumption it can actually modify. Q6 compares and combines them using a single common metric (Section 8).

**Central idea.** The starting hypothesis is that **rural transport energy consumption is not evenly distributed**: it is concentrated in a few segments, time slots and vehicle types, and the effect of any measure depends on where it is applied and on who generates the trip. For this reason **no single lever solves the problem on its own**: each one works only under certain conditions, and their savings overlap with those of the others. The study starts from a **common energy map** and evaluates all measures with the same metric, in order to identify **where and in which combination** they deliver the greatest savings and decarbonization at the lowest economic and social cost.

| Question | Main method | Model | Deliverable |
|---|---|---|---|
| Q1 | Graph with slopes, physical consumption model, graph neural network and attribution by trip origin | M1, M2 | Hourly consumption map by segment, broken down by trip origin |
| Q2 | Screening of levers with common criteria | M7 | Prioritized list of levers |
| Q3 | Mode choice and frequency optimization | M3, M4 | Net saving and occupancy threshold |
| Q4 | Penetration scenarios by fleet type | M5 | Reduction in petroleum products |
| Q5 | Consumption recalculation with new speeds and time penalty | M6 | Saving and time cost by segment |
| Q6 | Multi-objective optimization and Pareto frontier | M7 | Optimal package of measures |

### Testable hypotheses

| Hypothesis | Statement |
|---|---|
| H1 (Q1) | Consumption is concentrated in a few segments and time slots, and a relevant share of the territorial consumption on the main road is through traffic. |
| H2 (Q3) | There is an occupancy and slope threshold below which reinforcing the bus service increases net consumption. |
| H3 (Q3) | Electric fleets and minibuses shift that threshold; without a minimum coverage, the energy optimum cuts service in small settlements. |
| H4 (Q4) | The petroleum substitution potential differs widely between vehicle types and is limited by rural charging and refuelling infrastructure. |
| H5 (Q5) | The saving from lowering speeds depends on the number of fast segments and on traffic volume, and may be partly offset by traffic diverting to secondary roads. |
| H6 (Q6) | A combination of measures outperforms any single measure in saving per unit cost, although the savings are not additive. |

---

## 2. Definitions and scope

| Concept | Definition |
|---|---|
| Study area | Municipalities and concejos of the cuadrilla, plus an area of influence to capture inbound and outbound trips (to be confirmed). |
| Base year | Latest year with complete data on traffic counts, vehicle fleet and service. |
| Unit of analysis | Road segment × hour × day type. |
| Day types | School weekday, non-school weekday, Saturday, and Sunday or public holiday; with seasons if there is seasonal leisure traffic (for example, linked to the natural park). |
| Annual scaling | Annual result = sum of the day types weighted by the number of days of each type in the year. |
| Territorial consumption | Energy spent on the roads of the region by all vehicles, regardless of their origin. |
| Resident consumption | Energy of the trips made by the region's residents, including the segments outside the region. |
| Through traffic | Vehicles with neither origin nor destination in the region. |
| Primary energy | Energy at source, computed with a conversion factor per energy carrier (diesel, petrol, electricity, biofuels, etc.). |
| Sign convention | $\Delta E<0$ means saving; $\Delta E>0$ means an increase in consumption. |

---

## 3. Actual energy demand profile [Q1]

### What is obtained

An **energy consumption map** of the whole road network of the region, in kWh per segment and hour, with uncertainty intervals and broken down by vehicle type (car, van, truck, bus), by fuel and **by trip origin**. It includes aggregated profiles by municipality, by corridor and by time slot (commuting and school peaks versus off-peak), and two global indicators: **territorial consumption** and **resident consumption**.

### Difficulties specific to rural areas

- Slope makes the system **asymmetric**: climbing costs much more than descending, and average factors in g/km do not capture this.
- Only a small share of the roads has permanent sensors; secondary and regional roads usually remain unmeasured.
- A main road crosses the region, so **part of the traffic does not belong to local residents**. It must be separated in order to know on which consumption each measure can act.

### System boundaries and consumption attribution

**The problem.** If the study counted only the consumption of residents, it would not be possible to know which part of the map corresponds to each group. If it counted all the consumption of the territory, measures (for example, more buses in the region) could not reduce the consumption of those who do not live there. The problem is solved without choosing one of the two options: **consumption is computed within the region, but each flow is labelled according to who generates it**, and then each measure is applied only to the part on which it can act.

**Two indicators.** For each day type $d$ (with $N_d$ days per year):

$$
E_{\text{terr}} = \sum_{d} N_d \sum_{e \in E_{\text{com}}} \sum_{t=1}^{24} \sum_{k,\tau} E_{e,t,d}^{k,\tau} \tag{1}
$$

$$
E_{\text{res}} = \sum_{d} N_d \sum_{r \in \mathcal{R}_{\text{res}}} q_{r,d} \sum_{e \in \text{route}(r)} \varepsilon_{e,k(r)}\, L_e \tag{2}
$$

where $E_{\text{com}}$ are the segments of the region, $\mathcal{R}_{\text{res}}$ the resident trips, and the last sum also includes the segments **outside** the region. Equation (1) comes from the network map; Equation (2) must be built from the residents' trips. In addition, the **share of through traffic** is computed:

$$
s_{\text{through}} = \frac{E_{\text{terr}}^{\text{through}}}{E_{\text{terr}}}
$$

This share is an important result in itself: if it is large, local measures have a low ceiling and this must be stated.

**Trip types $\tau$.** Using origin-destination matrices, each flow that passes through the region is classified into one of four types:

| Trip type | Example |
|---|---|
| Internal | Resident moving within the region |
| Outbound resident | Resident worker travelling to Vitoria-Gasteiz |
| Inbound non-resident | Worker or visitor from outside coming to the region |
| Through | Vehicle crossing along the main road without stopping |

Freight with origin or destination in industrial estates of the region is identified separately, because it responds to different measures. The separation between residents and non-residents matters because **a resident's vehicle can be reached by fuel substitution (Q4)**, whereas that of an inbound non-resident can only be reached by public transport (Q3).

**Each solution acts on a different part.**

| Solution | What it acts on | Why |
|---|---|---|
| Q3, public transport | Internal trips, outbound resident trips and inbound non-resident trips. The **complete trip** is counted, including the segment outside the region | The bus replaces the whole journey, not only the part that crosses the region |
| Q4, petroleum substitution | Resident vehicles (internal and outbound), wherever they go | Local measures (subsidies, charging, service fleets) reach the fleet registered in the region, not the truck passing through |
| Q5, speeds | **All** traffic on the affected segments, including through traffic | The speed limit applies to everyone using the road; the competence usually belongs to another administration |

In this way the measures remain meaningful: none tries to reduce the consumption of those who do not live there, while the speed measure does, because through traffic is its main beneficiary. In Q3 the saving is reported separately **within the region** and **for the complete trip**; otherwise, the energy saved by those who leave the car to go to Vitoria would be lost.

**How to separate through traffic in practice.**

- Assign the origin-destination matrices to the network and label each flow by trip type.
- Calibrate this separation with **counts at the entry and exit points** of the region (a "cordon"). If the budget allows, sampling licence plates or devices at those points gives the through-traffic share with good reliability.
- For residents, use mobility surveys and the vehicle fleet by municipality. If access to odometer readings from vehicle inspections (ITV) is available, they greatly improve the estimate of kilometres per vehicle.
- **Do not use fuel sales** as a shortcut: with a main road, the petrol stations in the area sell mostly to those passing through and overestimate the residents' consumption.

### Methodology

**Step 1. Network and physical consumption per segment.**

- Extract the OpenStreetMap network as a **directed graph** $G=(V,E)$ (each direction is a distinct edge, $e_{ij}\neq e_{ji}$).
- Add altitude using a digital elevation model and compute the **slope** $\theta_e$ of each segment, smoothing the profile to avoid noise.
- Compute power with a **longitudinal dynamics model (vehicle specific power)**, for each vehicle type $k$, with bus mass depending on its occupancy and an operating speed $v_e$ per segment:

$$
P_{e,k} = v_e \left( m_k g C_r \cos\theta_e + m_k g \sin\theta_e + \tfrac{1}{2}\rho C_d A_k v_e^2 \right) \tag{3}
$$

- Downhill: idling in combustion engines and partial recovery in electric ones.
- Process GTFS and assign it to the network (*map-matching*) to obtain buses per segment and hour, including empty kilometres.
- **Validate** against reference factors (COPERT/HBEFA) and, if possible, against real consumption.

**Step 2. Total hourly flow on roads without sensors.**

- Gather existing counts, separate light and heavy vehicles, and subtract known buses.
- Build a physical *prior* by routing origin-destination matrices over the network.
- Train a **spatio-temporal graph neural network** that **predicts the total flow** $\hat{q}_{e,t,d}$, with a **flow conservation** penalty at through nodes (with slack in villages and industrial estates, which generate and attract trips):

$$
\mathcal{L} = \frac{1}{|E_{\text{obs}}|} \sum_{e \in E_{\text{obs}}} \left( \hat{q}_{e,t} - q_{e,t} \right)^2 + \lambda \sum_{v \in V_{\text{through}}} \left( \sum_{e \in \delta^-(v)} \hat{q}_{e,t} - \sum_{e \in \delta^+(v)} \hat{q}_{e,t} \right)^2
$$

- Always compare with simple models (pure origin-destination assignment, *gradient boosting*). If the neural network does not outperform them, this will be stated.
- **Spatial cross-validation** (holding out entire stations or zones), not random splits, and uncertainty intervals.

**Step 3. Attribution by trip type.** The neural network does not provide the breakdown by itself. The total flow is split using the proportions from the origin-destination assignment, calibrated with the cordon counts:

$$
\hat{q}_{e,t,d}^{\tau} = \pi_{e,t,d}^{\tau}\,\hat{q}_{e,t,d}, \qquad \sum_{\tau}\pi_{e,t,d}^{\tau}=1
$$

**Step 4. Baseline consumption.** For each segment, hour, day type, vehicle and trip type: $E_{e,t,d}^{k,\tau}=\hat{q}_{e,t,d}^{k,\tau}\,\varepsilon_{e,k}\,L_e$. It is broken down by fuel using the composition of the regional fleet, converted to primary energy, and the consumption of petroleum products is computed, which is the reference for Q4. It is scaled to a year with the weights $N_d$.

### Result

Map and hourly consumption profiles broken down by trip origin, diagnosis of **critical segments and time slots**, breakdown by vehicle and fuel, the **share of through traffic**, and the annual baseline of energy, petroleum products and CO₂ against which Q3 to Q6 are measured.

---

## 4. Technical, operational and demand-management levers [Q2]

### What is obtained

A catalogue of levers applicable to the region, with their **saving potential**, cost and feasibility estimated in a comparable way, and a selection of those that move on to detailed evaluation.

| Type | Levers | Where they act |
|---|---|---|
| Technical | Electrification, hybrids, biofuels (HVO, biodiesel), renewable gas, hydrogen; vehicle efficiency and lower mass; energy recovery downhill | Fleet of cars, vans, trucks and buses |
| Operational | Lower maximum speeds; frequencies and vehicle size; demand-responsive transport; eco-driving; route optimization and reduction of empty kilometres | Road network, lines and service fleets |
| Demand management | Shift to public transport; carpooling; teleworking and grouped services; active mobility and e-bikes on short trips; park-and-ride; fare policy | Everyday trips, mainly work and study |

### Methodology

- Rank the levers with the *avoid, shift, improve* framework: avoid trips, shift mode, and improve efficiency or fuel.
- For each one, estimate with the Q1 model the **maximum potential saving** on the consumption it actually affects (only the segments, vehicles and **trip types** to which it applies).
- Assess with common criteria: energy and petroleum saving, CO₂, cost, implementation time, administrative competences and social acceptance.
- Select those that move on to Q3, Q4, Q5 and Q6. The three main solutions are the shift to public transport, fuel substitution and network management; the rest are kept as a complement if the data allow.

### Result

Prioritized list of levers with their potential, cost and feasibility, and the justification of which ones are modelled in detail.

---

## 5. Net saving from the shift to public transport [Q3]

### What is obtained

The **net energy saving** (energy saved by the cars removed minus energy added by the additional buses) for each service design, and the conditions under which reinforcement pays off. It is reported **separately within the region and for the complete trip**.

### Methodology

**a) How many people would change mode.**

- Discrete choice model (logit) car-bus with waiting time, in-vehicle time, cost, access to the stop, car availability and trip purpose.
- **Waiting time.** With high frequencies (departures per hour $f_{l,t}$) it is approximated by $W_{l,t}\approx 30/f_{l,t}$ minutes, assuming random arrivals. On rural lines with few departures, people consult the timetable, so the **schedule mismatch** between the desired travel time and the nearest departure time is modelled.
- Calibration with mobility surveys (value of time) and, if possible, a small stated-preference survey in the region.
- Include **induced demand and rebound effect**: new trips generated by the improved service and road capacity taken up by other cars.
- Intermediate result: $\Delta q(\mathbf{f})$, cars removed per segment and hour for each frequency level, always as a **range**. It applies only to the trip types that the bus can replace; through traffic is not modified.

**b) Service redesign.**

- Decision variables: departures $f_{l,t}\in\mathbb{Z}_{\ge 0}$ per line and time slot.
- Net energy (with $\Delta E_{\text{net}}<0$ indicating saving), in primary energy. It is computed over the **complete trip** (all segments $E$ of the routes, including the bus journey **outside the region**, so as not to inflate the saving) and is also reported restricted to the segments of the region $E_{\text{com}}$:

$$
\Delta E_{\text{net}}(\mathbf{f}) = \sum_{d} N_d \sum_{t=1}^{24} \sum_{e \in E} \left[ \sum_{l \ni e} (f_{l,t} - f_{l,t}^{\text{base}})\, \varepsilon_{e,\text{bus}}(m_{l,t}) L_e - \Delta q_{e,t,d}^{\text{car}}(\mathbf{f})\, \varepsilon_{e,\text{car}} L_e \right] \tag{4}
$$

- **Minimum coverage** guaranteed in every settlement; without it the energy optimum would be to cut service.
- Multi-objective approach (energy, operating cost, user cost), with fleet, budget, headway and shift constraints.
- Solution by segment linearization, heuristics or decomposition by line, documenting the decision, and an iteration that closes the circularity **occupancy → mass → consumption → decision**.

**c) Service scenarios.**

| Scenario | What it represents | Key aspect |
|---|---|---|
| A. Conventional diesel | Current situation | High consumption uphill, no recovery |
| B. Electric fleet | Fleet electrification | Battery, downhill regeneration, energy mix |
| C. Minibuses | Smaller vehicles with higher frequency | Lower mass, lower capacity |
| D. Demand-responsive transport | Flexible service in low-demand areas and hours | On-demand routing, not fixed frequency |

### Result

Annual net saving in MWh and CO₂ per scenario with confidence interval, within the region and for the complete trip, optimal frequency curves, **critical occupancy threshold** by slope, time slot and vehicle, and the design that meets the minimum coverage.

---

## 6. Reduction of petroleum products through fuel substitution [Q4]

### What is obtained

The reduction in petrol and diesel consumption (and the associated CO₂) when replacing petroleum with other energy carriers, according to the **actual composition of the regional vehicle fleet**. Local measures reach **resident vehicles, wherever they go**; through traffic and non-resident vehicles remain outside their reach.

### Methodology

- Characterize the regional fleet by type (car, van, truck, bus), fuel and age, and assign it to the resident flows from Q1.
- Recalculate consumption with the physical model adapted to each technology (powertrain efficiency, regeneration, auxiliary loads).
- Measure in **end-to-end primary energy** and in CO₂ (well-to-wheel, or source-to-wheel), with a conversion factor per carrier. The origin of the electricity or fuel changes the result, so scenarios of the **evolution of the electricity mix** are included.
- Build **penetration scenarios**: percentage of the fleet replaced by type, with petroleum product consumption as the main indicator:

$$
D_{\text{pet}}(\boldsymbol{\alpha}) = \sum_{k}\sum_{c} (1-\alpha_{k,c})\; E^{k,c}_{\text{base}}\; \phi_{c} \tag{5}
$$

where $\alpha_{k,c}$ is the fraction of the consumption of vehicle $k$ and fuel $c$ that is replaced, and $\phi_c$ is the petroleum fraction of $c$.

- Check infrastructure (charging, refuelling), local **electricity grid capacity** and total cost of ownership.

| Alternative carrier | What must be evaluated | Rural constraint |
|---|---|---|
| Battery electric | Consumption per segment with regeneration, range on slopes, electricity mix | Charging in dispersed settlements, local grid power |
| Hybrid and plug-in hybrid | Split between electric and combustion kilometres | Home versus public charging |
| Advanced biofuels (HVO, biodiesel) | Use in existing trucks and buses | Availability and sustainability of the feedstock |
| Renewable gas (biomethane, CNG) | Feasibility in captive fleets and heavy vehicles | Refuelling infrastructure |
| Hydrogen and synthetic fuels | Overall efficiency and cost compared with batteries | Maturity, cost and low overall efficiency |

### Result

For each vehicle type, the alternative with the best balance between petroleum product reduction, cost and feasibility, and the expected annual regional reduction per penetration scenario, with an uncertainty range.

---

## 7. Operational management of the network: speeds and travel times [Q5]

### What is obtained

The **energy saving per segment** when lowering the maximum speed and the **travel-time penalty** that it implies, in order to decide on which segments it pays off. This measure acts on **all traffic on the affected segments, including through traffic**. As an order of magnitude, the literature cites a fuel saving of 10–15 % when lowering from 120 to 100–110 km/h on fast roads. **The study will compute it with its own model**, per segment and vehicle type, without taking it for granted.

### Methodology

- Identify candidate segments: motorways, dual carriageways and fast roads in the region or crossing it, and other segments where actual speed exceeds the efficient one. Verify which of them actually exist within the study scope.
- Recalculate $P_{e,k}$ (Equation (3)) and consumption with the new speed $v_e'$, using the flows from Q1.
- Compute the **time penalty** per segment and for the whole set of travellers:

$$
\Delta T_e = L_e\left(\frac{1}{v_e'}-\frac{1}{v_e}\right), \qquad \Delta T_{\text{trip}} = \sum_{e \in \text{route}} \Delta T_e
$$

- Define in advance what a **critical penalty** is: for example, a maximum increase in travel time per trip, or a limit for segments with school or emergency services. The threshold is set with the administrations and subjected to sensitivity analysis.
- **Traffic diversion.** A lower speed on the main road may push part of the traffic (including through traffic) onto secondary roads. Route change is modelled with a travel-time-sensitive assignment, and the additional consumption on those roads, which may be more winding or steeper, is deducted.
- Value the cost of the additional time using the value of time from Q3 and compare it with the energy and CO₂ saving (cost per MWh saved).
- Cross-check with Q3: a lower speed lengthens the car journey and may increase the attractiveness of the bus; the choice model captures this.
- Consider other segment adaptations: speed management on slopes, bus priority at intersections and platform improvements.
- Check the **administrative competence** of each segment, since the main road usually depends on another administration.

### Result

Prioritized list of segments with energy and CO₂ saving, travel-time increase, effect of traffic diversion, cost per MWh saved and assessment against the critical threshold, and the total regional saving. If there are few high-speed segments, the study will say so and quantify the real saving.

---

## 8. Optimal combination of the solutions [Q6]

### What is obtained

The **package of measures** from Q3, Q4 and Q5 that maximizes energy savings and decarbonization at the lowest economic and social cost, and the frontier of alternatives among which to decide.

### Methodology

- **Common metrics** for the three solutions, on the Q1 baseline: primary energy (MWh), petroleum products, CO₂, economic cost and social cost. Results are given both on the **territorial consumption** (Equation (1)) and on the **resident consumption** (Equation (2)).
- **Economic cost:** an evaluation horizon is set (for example, the useful life of vehicles and infrastructure), the investment is annualized (annualized or levelized cost), and operating and energy costs are added. The cost per MWh and per tonne of CO₂ avoided is computed.
- **Social cost:** territorial coverage, accessibility for households without a car or with lower income, additional travel time, and distribution of the effort among settlements.
- **Effects that are not additive.** Measures interact: for example, the saving from substituting fuels (Equation (5)) depends on how many cars remain after the shift (Equation (4)), and moderating speed changes the modal split. For this reason each combination is evaluated with the complete model and not as a sum of individual savings.
- **Ceiling of local measures.** The achievable saving is compared with total consumption to show which part remains outside the reach of the region because it is through traffic.
- **Multi-objective optimization** over the set of measures $\mathbf{x}$:

$$
\min_{\mathbf{x}}\; \Big( E(\mathbf{x}),\; D_{\text{pet}}(\mathbf{x}),\; C_{\text{econ}}(\mathbf{x}),\; C_{\text{soc}}(\mathbf{x}) \Big) \quad \text{subject to minimum coverage and budget}
$$

  solved as a **Pareto frontier**, with the marginal abatement cost curve (cost per MWh or per tonne of CO₂) to rank the measures.

- **Robustness:** global sensitivity analysis (Sobol or Morris) and uncertainty propagation (Monte Carlo); the recommended solutions must remain reasonable within the ranges of the uncertain parameters.
- **Time sequence:** separate immediate measures (speed management, service adjustments), medium-term measures (new public transport offer, service fleet) and long-term measures (renewal of the private fleet).

### Result

Pareto frontier with 2–3 recommended packages, the marginal cost curve of the measures, the implementation schedule, and recommendations for administrations and operators, with their confidence level.

---

## 9. Required data

| Block | Data | Likely source | Remarks |
|---|---|---|---|
| Road network | Roads, hierarchy and speed limits | OpenStreetMap | Check completeness on secondary roads |
| Relief | Digital elevation model | Copernicus DEM (30 m), SRTM; possible regional LiDAR | LiDAR greatly improves slope |
| Public transport | Timetables, stops and lines | GTFS from Open Data Euskadi and NAP | Check that it covers all lines |
| Bus occupancy | Passengers per segment and hour | Operator, counters or sampling | Critical data; may need to be requested |
| Traffic counts | Hourly intensity by vehicle type and speeds, on different day types | Diputación Foral de Álava, DGT, Basque Government | Few stations; check that they cover all day types |
| Cordon counts | Entries and exits of the region per hour, with licence plate or device sampling if possible | Diputación Foral de Álava, DGT; own sampling | Calibrates the through-traffic share |
| Demand | Origin-destination matrices, disaggregated by trip type | MITMA (mobile phone data) | Large zones, without clearly distinguishing mode or heavy vehicles |
| Calendar | School days, holidays and seasons | School and labour calendar | Define day types and their weights |
| Population and employment | Inhabitants, jobs, schools | INE, Eustat | Node variables; social profile |
| Vehicle fleet | Composition by fuel, type and age | DGT, Eustat | Basis for Q4 |
| Resident mileage | Kilometres per vehicle registered in the region | ITV readings, mobility surveys | Improves resident consumption; do not use fuel sales |
| Energy and electricity grid | Electricity mix and its evolution, grid and charging points; primary energy factors | Operators, Basque Government | Assessment of electrification |
| Consumption factors | Consumption and emissions per vehicle | COPERT, HBEFA | Validate the physical model |
| Behaviour | Mobility surveys, value of time | Basque Government, own survey | Calibration of the logit in Q3 and Q5 |
| Costs | Operation, energy prices, vehicle and infrastructure costs, discount rate | Operator, administrations, market | Economic analysis of Q6 |
| Territory | Municipal and concejo boundaries | Geoeuskadi, IGN | Aggregation and maps |

**Main data risk:** availability of actual occupancy and of counts on secondary roads and at the cordon. They should be requested from the Diputación and the operator as soon as possible. The request log is in [docs/data_requests.md](docs/data_requests.md).

---

## 10. Models generated

| Model | Input | Output | Answers |
|---|---|---|---|
| M1. Energy graph | OSM, DEM, GTFS | Slope and specific consumption per segment and vehicle | Q1 |
| M2. Vehicle flow and attribution | Counts, cordon counts, OD, road variables, day types | Hourly flow with uncertainty across the whole network, broken down by trip origin | Q1 |
| M3. Modal shift | Times, costs, surveys | $\Delta q(\mathbf{f})$ | Q3 |
| M4. Service optimization | M1–M3 plus constraints | Optimal frequencies and fleet scenarios | Q3 |
| M5. Energy substitution | Resident vehicle fleet, technologies, electricity mix | Petroleum product consumption per scenario | Q4 |
| M6. Speed and segments | M1, M2 and new speeds; route-change model | Saving, traffic diversion and time penalty per segment | Q5 |
| M7. Catalogue, integration and uncertainty | Results of M1–M6 and costs | Prioritized levers, Pareto frontier and intervals | Q2 and Q6 |

---

## 11. Risks and limitations

| Risk | Effect | Mitigation |
|---|---|---|
| Few counting stations | The neural network may not outperform simple models | Comparison with baselines; honesty in the article |
| Counts that do not cover all day types | Seasonality and weekends poorly represented | Request annual series; use typical days and sensitivity |
| Very large through traffic on the main road | Local measures have a low ceiling of saving on total consumption | Quantify the through-traffic share and report the saving on territorial consumption and on resident consumption |
| No cordon counts | The separation between residents and through traffic cannot be calibrated | Licence plate or device sampling at entries and exits |
| Coarse origin-destination matrices | Imprecise attribution by trip type | Combine with cordon counts, surveys and population variables |
| No occupancy data | Unreliable bus consumption | Request data from the operator; own sampling; sensitivity |
| Behaviour not calibrated locally | Uncertain modal shift | Short survey in the region; sensitivity analysis |
| DEM resolution | Erroneous slopes on short segments | Higher-resolution LiDAR; smoothing |
| Few high-speed segments | Speed management contributes little total saving | Verify the actual scope and extend to other adaptations |
| Traffic diversion to secondary roads | The Q5 saving is reduced or cancelled | Model route change and deduct the additional consumption |
| Assumptions on future technologies and electricity mix | Q4 results highly sensitive | Scenarios with ranges and sensitivity analysis |
| Valuation of social cost | Results depend on the chosen weights | Present the Pareto frontier rather than a single optimum |
| Over-interpretation of results | Decisions based on single figures | Always report intervals |

---

## 12. Technical tools

- **Geographic data:** `osmnx`, `geopandas`, `rasterio`, `networkx`.
- **Public transport:** `gtfs-kit` or `partridge`.
- **Machine learning and graphs:** `torch`, `torch_geometric`, `scikit-learn`.
- **Discrete choice:** `biogeme` or custom implementations.
- **Optimization:** `pyomo` with `HiGHS` or `SCIP`, and `pymoo` for multi-objective optimization and the Pareto frontier.
- **Sensitivity and uncertainty:** `SALib`.

---

## 13. Indicative schedule

| Stage | Content | Indicative duration |
|---|---|---|
| 1 | Study design, definitions and data requests | 1–2 months |
| 2 | Q1: network, consumption, flow and attribution by trip origin | 5–6 months |
| 3 | Q2: catalogue and screening of levers | 1–2 months, in parallel with stage 2 |
| 4 | Q3: modal shift, optimization and scenarios | 4–5 months |
| 5 | Q4 and Q5: energy substitution and speed management | 3 months, in parallel with stage 4 |
| 6 | Q6: integration, uncertainty and writing | 2–3 months |

These are indicative timelines for a small team and depend mainly on when the occupancy and count data are obtained.

---

## 14. Immediate next steps

1. Confirm the study area (municipalities and area of influence), the base year and the day types.
2. Request from the Diputación Foral de Álava, the Basque Government and the operator the data on counts (including cordon counts), GTFS, occupancy and vehicle fleet.
3. Build the energy graph (Q1) as a first proof of concept.
4. **Make a preliminary estimate of the through-traffic share** with the origin-destination matrices, to know the ceiling of local measures before going deeper.
5. Agree with the administrations on the critical travel-time penalty threshold (Q5) and the social cost criteria (Q6).
6. Decide whether to carry out a short mobility survey in the region.

---

## LOG. Steps (APUNTES PROPIOS)

### Mapas y carreteras
- SE DESCARGAN MAPAS PARA VER CARRETERAS DE GORBEIALDEA. SE VE QUE TODAS LAS CARRETERAS (MENOS BI-3941) TIENEN ALGUNA ESTACIÓN.
- SE DESCARGA MEDIANTE API LOS FLOWS. SE VE QUE NO ESTAN DISPONIBLE LOS DEL ÚLTIMO AÑO EN TODOS LOS NUCLEOS, PORESO SE VE LA CANTIDAD DE DATOS POR TRAMO. SIGUIENTE RESULTADOS: 
#### Cobertura de datos de flujos de tráfico (Open Data Euskadi)

Resultado de `python API_flow.py cobertura` (años 2010–2026) para los municipios con medidores identificados:
Arratzua-Ubarrundia, Zigoitia y Urkabustaiz.

- **Fuente:** API de tráfico de Open Data Euskadi (`/v1.0/flows/byYear/{año}/byMunicipality/...` y `.../byMeter/...`).
- **Años sin datos en ningún municipio:** 2010–2014, 2025 y 2026 (omitidos en las tablas; todos los valores son 0).
- **Total de registros 2010–2026:** 948.849.
- **Cobertura:** registros reales / registros esperados. Se supone 1 registro por franja de 30 min y medidor, es decir, 48 × 365 = 17.520 registros al año por medidor (100 % = sin huecos). Es un supuesto no confirmado en la documentación del API.
- **Medidores identificados:** Arratzua-Ubarrundia 4, Zigoitia 2, Urkabustaiz 4.
- **Municipios sin medidores propios localizados:** Aramaio, Legutio y Zuia.

---

1. Registros por municipio y año

| Municipio | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Arratzua-Ubarrundia | 20.600 | 39.262 | 57.774 | 58.573 | 58.863 | 57.644 | 60.724 | 49.572 | 56.013 | 49.647 |
| Zigoitia | 9.665 | 27.666 | 20.489 | 30.967 | 32.487 | 32.350 | 34.506 | 28.936 | 20.200 | 0 |
| Urkabustaiz | 20.916 | 32.877 | 31.428 | 1 | 30.747 | 28.747 | 21.819 | 17.889 | 18.487 | 0 |
| **TOTAL** | **51.181** | **99.805** | **109.691** | **89.541** | **122.097** | **118.741** | **117.049** | **96.397** | **94.700** | **49.647** |

2. Cobertura % (registros reales / esperados)

| Municipio | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Arratzua-Ubarrundia | 29,4 % | 56,0 % | 82,4 % | 83,6 % | 84,0 % | 82,3 % | 86,6 % | 70,7 % | 79,9 % | 70,8 % |
| Zigoitia | 27,6 % | 79,0 % | 58,5 % | 88,4 % | 92,7 % | 92,3 % | 98,5 % | 82,6 % | 57,6 % | 0,0 % |
| Urkabustaiz | 29,8 % | 46,9 % | 44,8 % | 0,0 % | 43,9 % | 41,0 % | 31,1 % | 25,5 % | 26,4 % | 0,0 % |
| **TOTAL** | **29,2 %** | **57,0 %** | **62,6 %** | **51,1 %** | **69,7 %** | **67,8 %** | **66,8 %** | **55,0 %** | **54,1 %** | **28,3 %** |

3. % del total de registros del periodo

Cada fila de municipio se calcula sobre el total de ese municipio; la fila TOTAL, sobre el total global (948.849).

| Municipio | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Arratzua-Ubarrundia | 4,0 % | 7,7 % | 11,4 % | 11,5 % | 11,6 % | 11,3 % | 11,9 % | 9,7 % | 11,0 % | 9,8 % |
| Zigoitia | 4,1 % | 11,7 % | 8,6 % | 13,1 % | 13,7 % | 13,6 % | 14,5 % | 12,2 % | 8,5 % | 0,0 % |
| Urkabustaiz | 10,3 % | 16,2 % | 15,5 % | 0,0 % | 15,2 % | 14,2 % | 10,8 % | 8,8 % | 9,1 % | 0,0 % |
| **TOTAL** | **5,4 %** | **10,5 %** | **11,6 %** | **9,4 %** | **12,9 %** | **12,5 %** | **12,3 %** | **10,2 %** | **10,0 %** | **5,2 %** |

4. Medidores con cobertura ≥ 80 %

| Municipio | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Arratzua-Ubarrundia (4 medidores) | 0 | 0 | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 1 |
| Zigoitia (2 medidores) | 0 | 1 | 0 | 2 | 2 | 2 | 2 | 2 | 1 | 0 |
| Urkabustaiz (4 medidores) | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **TOTAL (10 medidores)** | **0** | **2** | **3** | **4** | **5** | **4** | **4** | **3** | **3** | **1** |

---

5. Resumen

| Criterio | Mejor año | Valor |
|---|---|---|
| Más registros | **2019** | 122.097 (12,9 % del total) |
| Mayor cobertura global | **2019** | 69,7 % |
| Más medidores con cobertura ≥ 80 % | **2019** | 5 de 10 |

6. Lectura de los resultados

- **2019 es el año con más datos** según los tres criterios, y además es anterior a la pandemia, de modo que no refleja la caída de movilidad de 2020–2021.
- **Alternativas cercanas:** 2020 y 2021 tienen casi los mismos registros (118.741 y 117.049), pero son años atípicos por la pandemia. 2018 queda penalizado por Urkabustaiz, que tiene un solo registro ese año.
- **Años recientes:** 2022 y 2023 tienen unos 95.000 registros y 3 medidores bien cubiertos; 2024 solo tiene datos de Arratzua-Ubarrundia, y desde 2025 el API no devuelve flujos para estos municipios.
- **Urkabustaiz** nunca supera el 50 % de cobertura media (su máximo es 46,9 % en 2016). Solo tiene un medidor con cobertura ≥ 80 % en 2016, 2017 y 2019. Será necesario completar huecos con el día típico del medidor y asumir más incertidumbre.
- **Zigoitia** cae en 2023 (57,6 %) respecto a 2022 (82,6 %), por lo que 2023 no es buen año para ese municipio.
- **Compromiso con la definición de año base** del estudio ("último año con datos completos"): 2019 es el mejor en datos de tráfico, pero el más antiguo. Conviene comprobar si el parque de vehículos y la ocupación del autobús que se vayan a usar existen para ese año.

> **Pendiente:** esta tabla cubre solo los municipios con medidores propios en Álava. Las carreteras de Bizkaia de la cuadrilla (BI-xxxx) y los municipios sin medidores localizados (Aramaio, Legutio, Zuia) no están incluidos.