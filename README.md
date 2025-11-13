# CMEMS Data Analysis

This repository contains a set of Python tools for retrieving, processing, and analyzing oceanographic and atmospheric data from the **Copernicus Marine Environment Monitoring Service (CMEMS)**. The scripts support extraction and analysis of:

- **Sea Surface Temperature (SST)**
- **Sea Surface Salinity (SSS)**
- **Upwelling Index (UI)** based on wind stress

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

```
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
- \(	heta\): coastline angle (default **−32°**)  
- \(f\): Coriolis parameter  
- \(
ho_{air}, 
ho_{water}\): air and seawater densities  

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

```
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

## Requirements

Install dependencies:

```bash
pip install motuclient copernicusmarine netCDF4 pandas numpy openpyxl chardet
```

Python **3.9+** recommended.

---

## Notes & Recommendations

- A valid CMEMS account is required, and dataset license terms must be accepted.  
- For large temporal or spatial downloads, split requests by year.  
- Ensure latitude values are in degrees for UI computation.  
- CMEMS wind datasets may have hourly or daily resolution; adjust accordingly.  
- Ensure output directories exist or are created during script execution.

---

## License

This repository is intended for scientific and research use.
