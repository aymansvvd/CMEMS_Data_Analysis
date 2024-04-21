import netCDF4 as nc
import pandas as pd
import numpy as np
import chardet
from netCDF4 import Dataset
from datetime import datetime

# Path to CSV file (samples with Lon Lat and date)
csv_path = r"C:\\Path_to_CSV_file.csv"

# Detect the encoding of the CSV file
with open(csv_path, 'rb') as f:
    result = chardet.detect(f.read())

# Print the detected encoding
print(f"Detected encoding: {result['encoding']}")

# Path to the NetCDF file
file_path = r'C:\\Path_to_the_NetCDF_file.nc'

# Open the NetCDF file
with nc.Dataset(file_path, 'r') as dataset:
    # Display general information about the NetCDF dataset
    print(dataset)
    # Display information about dimensions in the dataset
    print("\nDimensions:")
    for dimname, dim in dataset.dimensions.items():
        print(f"{dimname}: {len(dim)}")
    # Display information about variables in the dataset
    print("\nVariables:")
    for varname, var in dataset.variables.items():
        print(f"{varname}: {var.shape} {var.units if 'units' in var.ncattrs() else ''}")
    # Display global attributes
    print("\nGlobal Attributes:")
    for attrname in dataset.ncattrs():
        print(f"{attrname}: {getattr(dataset, attrname)}")

# Function to retrieve SSS data
def get_sss(date_str, lon, lat):
    try:
        # Check if date_str is a valid string
        if pd.isna(date_str):
            return np.nan  # Handle missing date value as NaN
        date = datetime.strptime(date_str, '%d/%m/%Y')
        # Extract year, month, and day from the datetime object
        year = date.year
        month = date.month
        day = date.day
        # Check if the date components are valid
        if year < 1993 or year > 2024:
            return np.nan  # Invalid year, return NaN
        if month < 1 or month > 12:
            return np.nan  # Invalid month, return NaN
        if day < 1 or day > 31:
            return np.nan  # Invalid day, return NaN
        # Construct the file path based on the date components
        nc_file_path = f"C:\\SSS_{year}{month:02d}{day:02d}.nc"
        # Open the NetCDF file
        nc_data = Dataset(nc_file_path, 'r')
        # Extract the time values (timestamps in seconds) from the NetCDF data
        seconds = nc_data['time'][:]
        # Calculate the target timestamp based on the date components
        target_seconds = (datetime(year, month, day) - datetime(1993, 1, 1)).total_seconds()
        # Find the index in the 'seconds' array that corresponds to the closest timestamp to the target timestamp
        time_index = abs(seconds - target_seconds).argmin()
        # Find the indices in the longitude and latitude arrays that are closest to the provided 'lon' and 'lat' values
        lon_index = abs(nc_data['lon'][:] - lon).argmin()
        lat_index = abs(nc_data['lat'][:] - lat).argmin()
        # Extract the SSS value at the determined time, latitude, and longitude indices
        sss_value = nc_data['sss'][time_index, lat_index, lon_index]
        # Close the NetCDF file
        nc_data.close()
        
        return sss_value
    except (FileNotFoundError, ValueError):
        return np.nan

# Path to CSV file
csv_path = r"C:\\Path_to_CSV_file.csv"

# Read the CSV file into a DataFrame
df = pd.read_csv(csv_path, encoding=result['encoding'])

# Create an empty "SSS" column in the DataFrame
df['SSS'] = np.nan

# Use apply method to fill in the "SSS" values from NetCDF data
df['SSS'] = df.apply(lambda row: get_sss(date_str=row['Date'], lon=row['LONGITUDE'], lat=row['LATITUDE']), axis=1)

# Save the updated DataFrame back to a new CSV file (or overwrite the existing one)
updated_csv_path = r"C:\\Path_to_New_CSV_file.csv"
df.to_csv(updated_csv_path, index=False)