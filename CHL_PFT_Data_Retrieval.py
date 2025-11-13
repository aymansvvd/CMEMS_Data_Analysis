"""
CHL_PFT_Data_Retrieval.py

Retrieve CHL, PFTs, and optics variables from CMEMS plankton/optics products
using the `copernicusmarine` client. Saves one NetCDF file per day and per
product, organized as:

    <BASE_DIR>/<YEAR>/<YYYYMMDD>_plankton.nc
    <BASE_DIR>/<YEAR>/<YYYYMMDD>_optics.nc

You must provide valid CMEMS credentials (e.g. via environment variables
or as configured in the copernicusmarine client).
"""

import argparse
from pathlib import Path
from datetime import datetime, timedelta

import copernicusmarine
import xarray as xr


# Default variable lists (same as your original script)
DEFAULT_PLANKTON_VARS = [
    "CHL", "CHL_uncertainty", "flags",
    "DIATO", "DINO", "HAPTO", "GREEN", "PROKAR", "PROCHLO", "MICRO", "NANO", "PICO",
    "DIATO_uncertainty", "DINO_uncertainty", "HAPTO_uncertainty", "GREEN_uncertainty",
    "PROKAR_uncertainty", "PROCHLO_uncertainty", "MICRO_uncertainty",
    "NANO_uncertainty", "PICO_uncertainty",
]

DEFAULT_OPTICS_VARS = [
    "BBP", "BBP_uncertainty", "flags", "CDM", "CDM_uncertainty"
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Retrieve CHL/PFT and optics data from CMEMS using copernicusmarine."
    )

    parser.add_argument(
        "--plankton-base-dir",
        type=str,
        required=True,
        help="Base directory where plankton NetCDF files will be stored."
    )
    parser.add_argument(
        "--optics-base-dir",
        type=str,
        required=False,
        help="Base directory where optics NetCDF files will be stored (optional)."
    )

    parser.add_argument(
        "--lat-min", type=float, required=True,
        help="Minimum latitude of the region of interest."
    )
    parser.add_argument(
        "--lat-max", type=float, required=True,
        help="Maximum latitude of the region of interest."
    )
    parser.add_argument(
        "--lon-min", type=float, required=True,
        help="Minimum longitude of the region of interest."
    )
    parser.add_argument(
        "--lon-max", type=float, required=True,
        help="Maximum longitude of the region of interest."
    )

    parser.add_argument(
        "--start-date",
        type=str,
        required=True,
        help="Start date (YYYY-MM-DD)."
    )
    parser.add_argument(
        "--end-date",
        type=str,
        required=True,
        help="End date (YYYY-MM-DD), inclusive."
    )

    parser.add_argument(
        "--plankton-dataset-id",
        type=str,
        required=True,
        help="CMEMS dataset ID for plankton/CHL/PFT product."
    )
    parser.add_argument(
        "--optics-dataset-id",
        type=str,
        required=False,
        help="CMEMS dataset ID for optics product (optional)."
    )

    parser.add_argument(
        "--plankton-vars",
        type=str,
        nargs="*",
        default=DEFAULT_PLANKTON_VARS,
        help="List of plankton variables to retrieve (overrides defaults)."
    )
    parser.add_argument(
        "--optics-vars",
        type=str,
        nargs="*",
        default=DEFAULT_OPTICS_VARS,
        help="List of optics variables to retrieve (overrides defaults)."
    )

    return parser.parse_args()


def date_range(start: datetime, end: datetime):
    """Yield datetime objects from start to end inclusive, step 1 day."""
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def retrieve_daily_dataset(
    dataset_id: str,
    variables: list[str],
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    day: datetime,
) -> xr.Dataset:
    """Retrieve one day's subset of a dataset via copernicusmarine."""
    start_iso = day.strftime("%Y-%m-%d 00:00:00")
    end_iso = (day + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")

    ds = copernicusmarine.open_dataset(
        dataset_id=dataset_id,
        minimum_latitude=lat_min,
        maximum_latitude=lat_max,
        minimum_longitude=lon_min,
        maximum_longitude=lon_max,
        start_datetime=start_iso,
        end_datetime=end_iso,
        variables=variables,
    )
    return ds


def main() -> None:
    args = parse_args()

    plankton_base = Path(args.plankton_base_dir)
    plankton_base.mkdir(parents=True, exist_ok=True)

    optics_base = None
    if args.optics_base_dir:
        optics_base = Path(args.optics_base_dir)
        optics_base.mkdir(parents=True, exist_ok=True)

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    for day in date_range(start, end):
        ymd = day.strftime("%Y%m%d")
        year_str = day.strftime("%Y")

        print(f"Processing day {ymd}...")

        # ----- PLANKTON -----
        try:
            ds_plankton = retrieve_daily_dataset(
                dataset_id=args.plankton_dataset_id,
                variables=args.plankton_vars,
                lat_min=args.lat_min,
                lat_max=args.lat_max,
                lon_min=args.lon_min,
                lon_max=args.lon_max,
                day=day,
            )

            out_dir = plankton_base / year_str
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{ymd}_plankton.nc"
            ds_plankton.to_netcdf(out_path)
            print(f"  Plankton saved to {out_path}")
        except Exception as e:
            print(f"  [WARNING] Could not retrieve plankton data for {ymd}: {e}")

        # ----- OPTICS (optional) -----
        if optics_base and args.optics_dataset_id:
            try:
                ds_optics = retrieve_daily_dataset(
                    dataset_id=args.optics_dataset_id,
                    variables=args.optics_vars,
                    lat_min=args.lat_min,
                    lat_max=args.lat_max,
                    lon_min=args.lon_min,
                    lon_max=args.lon_max,
                    day=day,
                )

                out_dir = optics_base / year_str
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{ymd}_optics.nc"
                ds_optics.to_netcdf(out_path)
                print(f"  Optics saved to {out_path}")
            except Exception as e:
                print(f"  [WARNING] Could not retrieve optics data for {ymd}: {e}")

    print("Done.")


if __name__ == "__main__":
    main()
