import getpass
import subprocess
import motuclient
import shlex
from datetime import datetime, timedelta

# CMEMS User Parameters example
USERNAME = "USERNAME"
PASSWORD = "PASSWORD"

# API Parameters example
serviceID = "SST_GLO_SST_L4_REP_OBSERVATIONS_010_024-TDS"
productID = "C3S-GLO-SST-L4-REP-OBS-SST"
lon = (-9.86, -7.39)
lat = (36.88, 41.87)
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
        out_name = f"SST_{current_date.strftime('%Y%m%d')}.nc" # NetCDF file format
        query = [
            "python", "-m", "motuclient.motuclient",
            "--motu", "https://my.cmems-du.eu/motu-web/Motu",
            "--service-id", serviceID,
            "--product-id", productID,
            "--longitude-min", str(lon[0]),
            "--latitude-min", str(lat[0]),
            "--latitude-max", str(lat[1]),
            "--date-min", current_date.strftime('%Y-%m-%d %H:%M:%S'),
            "--date-max", (current_date + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
            "--variable", "analysed_sst",
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