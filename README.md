# CMEMS Data Analysis

This repository contains Python tools for retrieving, processing, and analyzing oceanographic and atmospheric data from the Copernicus Marine Environment Monitoring Service (CMEMS). Supported variables include:

- Sea Surface Temperature (SST)
- Sea Surface Salinity (SSS)
- Upwelling Index (UI)
- Chlorophyll-a (CHL)
- Plankton Functional Types (PFTs)
- Optical properties (BBP, CDM, etc.)

Each module operates independently but can be combined for a complete workflow.

---

## 1. Sea Surface Temperature (SST)

### SST_Data_Retrieval.py

Retrieves daily SST NetCDF files using CMEMS API parameters. Files are saved as:

```
SST_YYYYMMDD.nc
```

**Usage:**
1. Provide CMEMS `USERNAME` and `PASSWORD`.
2. Configure:
   - `serviceID`
   - `productID`
   - Geographic bounding box (`lon`, `lat`)
   - Date range (`start_year`, `end_year`)
3. Run the script to download SST files.

---

### SST_Data_Processing.py

Extracts SST values from downloaded NetCDF files for sample positions stored in a CSV.

**Workflow:**
1. Reads sample table with latitude, longitude, and date.
2. Loads corresponding `SST_YYYYMMDD.nc`.
3. Extracts the nearest SST grid value.
4. Converts SST from Kelvin to Celsius.
5. Outputs updated CSV containing a new `SST` column.

---

## 2. Sea Surface Salinity (SSS)

### SSS_Data_Retrieval.py

Retrieves SSS fields from CMEMS. It follows the same structure and usage as the SST retrieval script.

### SSS_Data_Processing.py

Extracts SSS from NetCDF files into a CSV table. Usage and logic mirror SST processing.

---

## 3. Upwelling Index (UI)

The Upwelling Index quantifies wind-driven vertical transport along a coastline. It is computed from:

- Wind stress components
- Coriolis parameter
- Coastline angle

### Mathematical Formulation

Wind stress components:

```
tau_x = rho_air * C_d * |U| * u
tau_y = rho_air * C_d * |U| * v
```

Coriolis parameter:

```
f = 2 * Omega * sin(latitude)
```

Upwelling Index:

```
UI = (tau_x * sin(theta) - tau_y * cos(theta)) / (rho_water * f)
```

Where:
- `u`, `v` = wind components  
- `|U|` = wind speed  
- `theta` = coastline angle (default -32°)  
- `rho_air`, `rho_water` are densities  
- `Omega` is Earth's rotation rate  

---

### UI_Data_Retrieval.py

Downloads wind fields (eastward and northward wind) for selected locations using `copernicusmarine`.

**Features:**
- Coordinates provided via CSV or built-in list
- User-control of dataset ID and time range
- One CSV per location

**Example:**

```bash
python UI_Data_Retrieval.py   --output-dir C:\Data\ui_wind   --coords-file C:\Data\stations.csv   --lat-col LATITUDE   --lon-col LONGITUDE   --id-col STATION_ID   --dataset-id cmems_obs-wind_glo_phy_my_l4_0.125deg_PT1H   --start 2013-01-01 00:00:00   --end   2023-12-31 23:00:00
```

---

### UI_Data_Processing.py

Computes the Upwelling Index from wind CSV or Excel files.

**Features:**
- Supports CSV or multi-sheet Excel
- User-defined column names
- Configurable coastline angle
- Outputs Excel or CSV

**Example:**

```bash
python UI_Data_Processing.py   --input C:\data\wind.csv   --output C:\data\wind_ui.csv   --date-col time   --lat-col latitude   --u-col eastward_wind   --v-col northward_wind   --theta-deg -32
```

---

## 4. Chlorophyll-a (CHL), Plankton Functional Types (PFTs), and Optics

These scripts extract CHL, PFTs, and optical variables from CMEMS products and match them to sample coordinates and dates.

---

### CHL_PFT_Data_Retrieval.py

Retrieves daily plankton and/or optics fields and stores them as:

```
<BASE_DIR>/<YEAR>/<YYYYMMDD>_plankton.nc
<BASE_DIR>/<YEAR>/<YYYYMMDD>_optics.nc
```

**Features:**
- Separate plankton and optics dataset configuration
- Custom variable lists
- Custom bounding box and date range

**Example:**

```bash
python CHL_PFT_Data_Retrieval.py   --plankton-base-dir C:\PLANKTON_BASE_DIR   --optics-base-dir   C:\OPTICS_BASE_DIR   --lat-min 36 --lat-max 45   --lon-min -12 --lon-max -5   --start-date 2016-01-01   --end-date   2016-12-31   --plankton-dataset-id YOUR_PLANKTON_DATASET_ID   --optics-dataset-id   YOUR_OPTICS_DATASET_ID
```

---

### CHL_PFT_Data_Processing.py

Matches CHL, PFT, and optics variables to sample locations.

**Input Requirements:**
- Year, Month, Day
- Latitude, Longitude

**Operations:**
1. Finds correct daily NetCDF file(s)
2. Chooses nearest model grid point
3. Extracts available plankton and optics variables
4. Saves updated table with new columns

**Example:**

```bash
python CHL_PFT_Data_Processing.py   --input C:\INPUT.xlsx   --plankton-base-dir C:\PLANKTON_BASE_DIR   --optics-base-dir   C:\OPTICS_BASE_DIR   --output-xlsx C:\OUTPUT.xlsx   --output-csv  C:\OUTPUT.csv
```

---

## Requirements

Install dependencies:

```bash
pip install motuclient copernicusmarine netCDF4 pandas numpy openpyxl chardet xarray
```

Python 3.9+ recommended.

---

## Notes

- CMEMS credentials required
- Daily downloads may take time for long time ranges
- Latitude must be in degrees
- Ensure output directories exist or will be created

---

## License

For scientific and research use.
