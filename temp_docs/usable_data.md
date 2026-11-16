# Usable Data Log

## 1. Open data
 
These sources can be downloaded directly. Record the exact version, access date and licence in `data/README.md` when each is downloaded.
 
| ID | Dataset | Source | Version | URL | Data |
|---|---|---|---|---|---|
PDF.01|Road Map v.1|Diputación de Álava|2013|https://web.araba.eus/es/carreteras/mapas-de-carreteras|Road_ID, Road_Type|
PDF.02|Road Map v.2|Diputación de Álava|2025|https://web.araba.eus/es/carreteras/mapas-de-carreteras|Control_Coord|
XLSX.01|Road Data v.1|Diputación de Álava|2025|https://web.araba.eus/es/carreteras/mapas-de-carreteras|ROAD_long, IMD_mean(temporal, transport type, type of day and number of transports distribution), KM_distribution
GPKG.01|Municipality Map v.1|GeoAraba|-|https://geo.araba.eus/deskargak/Cartografia_Base/DivisionesAdministrativas/Informaci%C3%B3n_vectorial/|MUNICIPALITY_lim|
GPKG.02|Road Map v.3|GeoAraba|2026|https://geo.araba.eus/deskargak/Cartografia_Base/Cartografia_5000_BTA5000/BTA5000_Territorio_Continuo/SHP_Publicacion_Septiembre_2026/|Stations_Coord, Stations_Type|
CSV.01|Stations Data v.1|Opendata Euskadi|2026|https://opendata.euskadi.eus/catalogo/-/datos-trafico-semanales-estaciones-aforo/|Road_ID, Road_Type|
PY.01|API_flow|Opendata Euskadi|2026|https://opendata.euskadi.eus/api-traffic/?api=traffic&num=3#/flows|IMD|

## 2. Modified data
 
These data has been mmodified from the Open Data.
 
| ID | Dataset | Source | Methodology |Data |
|---|---|---|---|---|
|M.GPKG.01|MRoad Map v.1|GPKG.02|Filter by Road, Cut by Gorbeialdea|Road_ID|
|M.XLSX.01|MRoad Data v.1|XLSX.01|Filter by Gorbeialdea´s roads|Related Stations|
