# CMEMS Data Analysis

This repository contains Python scripts for retrieving, processing, and analyzing oceanographic data from the Copernicus Marine Environment Monitoring Service (CMEMS).

## Files:

### SST_Data_Retrieval.py

This script retrieves oceanographic data from CMEMS using the provided CMEMS User Parameters and API Parameters. It downloads Sea Surface Temperature (SST) data in NetCDF format for a specified geographical region and time period.

#### Usage:
1. Update the `USERNAME` and `PASSWORD` variables with your CMEMS credentials.
2. Modify the `serviceID`, `productID`, `lon`, `lat`, `start_year`, and `end_year` variables to specify the desired CMEMS dataset, geographical region, and time period.
   - Ensure that the selected `lon` and `lat` values fall within the bounds of water pixels in the satellite imagery.
   - Confirm that the chosen `start_year` and `end_year` are accessible for the selected product.
4. Run the script to retrieve the data. The downloaded files will be saved in the specified output directory.

### SST_Data_Processing.py

This script processes and analyzes oceanographic data retrieved from CMEMS. It reads data from NetCDF and CSV files, extracts relevant information, and performs data processing tasks such as converting SST from Kelvin to Celsius and saving the processed data back to a CSV file.

#### Usage:
1. Update the `csv_path` variable with the path to your CSV file containing samples with longitude, latitude, and date information.
2. Update the `file_path` variable with the path to your NetCDF file containing SST data.
3. Run the script to process the data. It will extract SST values for each sample location from the NetCDF file, convert them from Kelvin to Celsius, and save the updated data to a new CSV file.

### SSS_Data_Retrieval.py

This script retrieves oceanographic data from CMEMS for Sea Surface Salinity (SSS) using the provided CMEMS User Parameters and API Parameters. It downloads SSS data in NetCDF format for a specified geographical region and time period.

#### Usage:
1. Update the `USERNAME` and `PASSWORD` variables with your CMEMS credentials.
2. Modify the `serviceID`, `productID`, `lon`, `lat`, `start_year`, and `end_year` variables to specify the desired CMEMS dataset, geographical region, and time period.
   - Ensure that the selected `lon` and `lat` values fall within the bounds of water pixels in the satellite imagery.
   - Confirm that the chosen `start_year` and `end_year` are accessible for the selected product.
4. Run the script to retrieve the data. The downloaded files will be saved in the specified output directory.
