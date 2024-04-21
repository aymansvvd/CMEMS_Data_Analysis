import getpass
import subprocess
import motuclient
import shlex
from datetime import datetime, timedelta

# CMEMS User Parameters example
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"

# API Parameters for Sea Surface Salinity (SSS) data
serviceID = "MULTIOBS_GLO_PHY_S_SURFACE_MYNRT_015_013"
productID = "cmems_obs-mob_glo_phy-sss_my_multi_P1D"

# Coordinates for the area of interest
lon = (-9.86, -7.39)
lat = (36.88, 41.87)

# Time range
start_year = 2017  # Starting year
end_year = 2022    # Ending year

# Function to get the last day of a given month
def last_day_of_month(year, month):
    if month == 12:
        return datetime(year, month, 31)
    return datetime(year, month + 1, 1) - timedelta(days=1)

while start_year <= end_year:
    current_date = datetime(start_year, 1, 1, 0, 0, 0)
    while current_date <= last_day_of_month(start_year, 12):
        # Modify the 'out_name' format to match the desired format
        out_name = f"SSS_{current_date.strftime('%Y%m%d')}.nc" # NetCDF file format
        query = [
            "python", "-m", "motuclient.motuclient",
            "--motu", "https://my.cmems-du.eu/motu-web/Motu",
            "--service-id", serviceID,
            "--product-id", productID,
            "--longitude-min", str(lon[0]),
            "--longitude-max", str(lon[1]),
            "--latitude-min", str(lat[0]),
            "--latitude-max", str(lat[1]),
            "--date-min", current_date.strftime('%Y-%m-%d'),
            "--date-max", (current_date + timedelta(days=1)).strftime('%Y-%m-%d'),
            "--variable", "so",  # Use "so" for Sea Surface Salinity
            "--out-dir", "C:\\Directory",  # Output directory
            "--out-name", out_name,
            "--user", USERNAME,
            "--pwd", shlex.quote(PASSWORD)  # Properly quote the password
        ]

        print(f"============== Running request on {current_date} ==============")
        print(" ".join(query))

        subprocess.run(query, shell=True)

        current_date += timedelta(days=1)

    start_year += 1

print(f"============== Download completed! All files are in your specified output directory ==============")