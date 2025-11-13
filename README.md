# CMEMS Data Analysis

This repository contains a set of Python tools for retrieving, processing, and analyzing oceanographic and atmospheric data from the **Copernicus Marine Environment Monitoring Service (CMEMS)**. The scripts support extraction and analysis of:

- **Sea Surface Temperature (SST)**
- **Sea Surface Salinity (SSS)**
- **Upwelling Index (UI)** based on wind stress
- **Chlorophyll-a (CHL)**, **Plankton Functional Types (PFTs)**, and associated **optical properties**

Each module operates independently but can be combined into a unified oceanographic data-processing workflow.

---

## 1. Sea Surface Temperature (SST)

### SST_Data_Retrieval.py

Retrieves **daily SST NetCDF files** from CMEMS based on user-defined:

- CMEMS credentials  
- Dataset and product IDs  
- Geographic bounding box  
- Time range  

Files are saved using the naming format:

```text
SST_YYYYMMDD.nc
```

#### Usage

1. Update CMEMS `USERNAME` and `PASSWORD`.
2. Set:
   - `serviceID`
   - `productID`
   - `lon` / `lat` bounds
   - `start_year`, `end_year`
3. Verify that the selected region corresponds to ocean pixels and that data exist for the chosen period.
4. Run the script to download SST data.

---

### SST_Data_Processing.py

Extracts SST values for sample points provided in a CSV file. For each record (latitude, longitude, date):

1. Identifies the corresponding `SST_YYYYMMDD.nc` file  
2. Extracts the SST value from the nearest grid point  
3. Converts Kelvin to Celsius  
4. Outputs a new CSV file including a new `SST` column  

#### Usage

1. Set `csv_path` to your sample CSV file.  
2. Set the directory containing SST NetCDF files.  
3. Run the script to produce a processed CSV with SST values.

---

## 2. Sea Surface Salinity (SSS)

### SSS_Data_Retrieval.py

Retrieves SSS data from CMEMS for a user-defined region and period.  
This script follows the same pattern as **SST_Data_Retrieval.py**.

### SSS_Data_Processing.py

Processes SSS data by extracting salinity values from NetCDF files for each sample in a CSV.  
The workflow is identical to **SST_Data_Processing.py**.

---

## 3. Upwelling Index (UI)

The Upwelling Index quantifies wind-driven vertical transport along a coastline. It is derived from wind stress and the Coriolis parameter:

\[
\tau_x = \rho_{air} C_d |U| u,\quad \tau_y = \rho_{air} C_d |U| v
\]

\[
f = 2\Omega\sin(\phi)
\]

\[
UI = \frac{\tau_x \sin\theta - \tau_y \cos\theta}{\rho_{water} f}
\]

Where:
- \(u, v\): eastward and northward wind components  
- \(|U|\): wind magnitude  
- \(\theta\): coastline angle (default **−32°**)  
- \(f\): Coriolis parameter  
- \(\rho_{air}, \rho_{water}\): air and seawater densities  

Two scripts support the full UI workflow.

---

### UI_Data_Retrieval.py

Downloads wind variables from a CMEMS atmospheric product using the `copernicusmarine` Python client.  
Features include:

- Coordinate input from a **CSV file**  
- Optional built-in fallback station list  
- Custom dataset ID and time range  
- User-defined extraction radius  
- One CSV output per station  

Each output file includes:

```text
time, eastward_wind, northward_wind, latitude, longitude, station_id
```

#### Usage — with coordinate CSV

```bash
python UI_Data_Retrieval.py     --output-dir "C:\Data\ui_wind"     --coords-file "C:\Data\stations.csv"     --lat-col LATITUDE     --lon-col LONGITUDE     --id-col STATION_ID     --dataset-id "cmems_obs-wind_glo_phy_my_l4_0.125deg_PT1H"     --start "2013-01-01 00:00:00"     --end   "2023-12-31 23:00:00"
```

#### Usage — using built-in coordinates

```bash
python UI_Data_Retrieval.py --output-dir "C:\Data\ui_wind"
```

---

### UI_Data_Processing.py

Computes the Upwelling Index from wind data stored in:

- A CSV file  
- A single-sheet Excel file  
- A multi-sheet Excel workbook  

Supports custom:

- Date column  
- Latitude column  
- Eastward wind column  
- Northward wind column  
- Coastline angle  

Outputs either CSV or Excel depending on the file extension.

#### Usage — CSV input

```bash
python UI_Data_Processing.py     --input  "C:\Data\wind_point_1.csv"     --output "C:\Data\wind_point_1_ui.csv"     --date-col time     --lat-col latitude     --u-col eastward_wind     --v-col northward_wind     --theta-deg -32
```

#### Usage — Excel, multiple sheets

```bash
python UI_Data_Processing.py     --input  "C:\Data\wind_points.xlsx"     --output "C:\Data\wind_points_ui.xlsx"     --sheets Sheet1 Sheet2     --date-col time     --lat-col LATITUDE     --u-col eastward_wind     --v-col northward_wind     --theta-deg -32
```

---

## 4. Chlorophyll-a (CHL), Plankton Functional Types (PFTs) and Optics

These tools extract **Chlorophyll-a**, **Plankton Functional Types (PFTs)**, and **optical properties** (e.g. BBP, CDM) from CMEMS plankton and optics products and collocate them with in situ sample positions and dates.

The workflow is:

1. Download daily or gridded plankton/optics fields from CMEMS (e.g. with `CHL_PFT_Data_Retrieval.py`).  
2. Extract CHL, PFT and optics variables at sample locations and dates using `CHL_PFT_Data_Processing.py`.

### CHL_PFT_Data_Retrieval.py

Retrieves CHL, PFTs and/or optics variables from CMEMS plankton and optics products using the `copernicusmarine` client.  
Data are saved as daily NetCDF files organised by year so they can be picked up easily by the processing script.

Features:

- Separate configuration for **plankton** and **optics** products  
- User-defined latitude/longitude bounding box  
- Start and end date  
- Custom variable lists for each product  
- One NetCDF file per day and per product, named with the date (`YYYYMMDD_*.nc`) in a `<BASE_DIR>/<YEAR>/` folder

Example usage:

```bash
python CHL_PFT_Data_Retrieval.py     --plankton-base-dir "C:\PLANKTON_BASE_DIR"     --optics-base-dir   "C:\OPTICS_BASE_DIR"     --lat-min 36.0 --lat-max 45.0     --lon-min -12.0 --lon-max -5.0     --start-date 2016-01-01     --end-date   2016-12-31     --plankton-dataset-id YOUR_PLANKTON_DATASET_ID     --optics-dataset-id   YOUR_OPTICS_DATASET_ID
```

You can also customise the plankton and optics variable lists using command-line options if needed.

---

### CHL_PFT_Data_Processing.py

Reads an input table (Excel or CSV) with at least the following columns:

- `Year`, `Month`, `Day`  
- `LATITUDE`, `LONGITUDE`  

For each row, it:

1. Locates the appropriate daily plankton and optics NetCDF files in the given base directories  
2. Finds the nearest model grid point to the station position (within a configurable tolerance)  
3. Extracts CHL, PFT, and optics variables  
4. Writes the results back to Excel and/or CSV, adding new columns for each extracted variable

Default variables include:

- **Plankton**:  
  `CHL`, `CHL_uncertainty`, `flags`,  
  `DIATO`, `DINO`, `HAPTO`, `GREEN`, `PROKAR`, `PROCHLO`, `MICRO`, `NANO`, `PICO`,  
  and their corresponding `_uncertainty` fields.
- **Optics**:  
  `BBP`, `BBP_uncertainty`, `flags` (renamed to `flags_optics` in the output),  
  `CDM`, `CDM_uncertainty`.

Example usage:

```bash
python CHL_PFT_Data_Processing.py     --input "C:\INPUT_XLSX.xlsx"     --plankton-base-dir "C:\PLANKTON_BASE_DIR"     --optics-base-dir   "C:\OPTICS_BASE_DIR"     --output-xlsx "C:\OUTPUT_XLSX.xlsx"     --output-csv  "C:\OUTPUT_CSV.csv"
```

The script will:

- Group samples by date  
- Search for matching NetCDF files in the plankton and optics base directories (organised by year)  
- Extract all available variables for each sample  
- Save the updated table with added CHL, PFTs and optics columns.

---

## Requirements

Install dependencies:

```bash
pip install motuclient copernicusmarine netCDF4 pandas numpy openpyxl chardet xarray
```

Python **3.9+** is recommended.

---

## Notes & Recommendations

- A valid CMEMS account is required, and dataset licence terms must be accepted.  
- For large temporal or spatial downloads, consider splitting requests by year.  
- Ensure latitude values are in degrees for UI and CHL/PFT calculations.  
- CMEMS datasets may have hourly or daily resolution; adjust temporal sampling in retrieval scripts accordingly.  
- Ensure output directories exist or are created during script execution.

---

## License

This repository is intended for scientific and research use.
