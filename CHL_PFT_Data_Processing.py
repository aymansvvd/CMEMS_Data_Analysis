"""
CHL_PFT_Data_Processing.py

Extract CHL, PFTs and optics variables from plankton/optics NetCDF files
and collocate them with in situ sample positions/dates.

- Input: Excel or CSV table with Year, Month, Day, LATITUDE, LONGITUDE
- NetCDF: stored under base_dir/<year>/*.nc (files containing YYYYMMDD in the name)
- Output: Excel and/or CSV with additional CHL/PFT/optics columns.
"""

import os
import glob
import argparse
from typing import List, Dict

import numpy as np
import pandas as pd
import xarray as xr
import warnings

# Silence that xarray dims FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning, module="xarray")

# ----------------- DEFAULT VARIABLES -----------------
DEFAULT_PLANKTON_VARS: List[str] = [
    "CHL", "CHL_uncertainty", "flags",
    "DIATO", "DINO", "HAPTO", "GREEN", "PROKAR", "PROCHLO", "MICRO", "NANO", "PICO",
    "DIATO_uncertainty", "DINO_uncertainty", "HAPTO_uncertainty", "GREEN_uncertainty",
    "PROKAR_uncertainty", "PROCHLO_uncertainty", "MICRO_uncertainty",
    "NANO_uncertainty", "PICO_uncertainty"
]

DEFAULT_OPTICS_VARS: List[str] = [
    "BBP", "BBP_uncertainty", "flags", "CDM", "CDM_uncertainty"
]

# For variable names we need to rename (to avoid collisions)
RENAME_OUT = {
    # optics flags -> 'flags_optics'
    ("optics", "flags"): "flags_optics",
}

# ----------------- DEFAULT COLUMN NAMES -----------------
COL_YEAR = "Year"
COL_MONTH = "Month"
COL_DAY = "Day"
COL_LAT = "LATITUDE"
COL_LON = "LONGITUDE"

# ----------------- NETCDF CONVENTIONS -----------------
LAT_NAME = "lat"
LON_NAME = "lon"
TIME_NAME = "time"   # if present

# Nearest-neighbour tolerance (deg)
DEFAULT_TOL_DEG = 0.05


# ----------------- HELPERS -----------------
def file_candidates_for_date(base_dir: str, y: int, m: int, d: int):
    """Find files in base_dir/<year>/ that contain YYYYMMDD in the filename."""
    ymd = f"{y:04d}{m:02d}{d:02d}"
    year_dir = os.path.join(base_dir, f"{y:04d}")
    patterns = [
        os.path.join(year_dir, f"{ymd}_*.nc"),
        os.path.join(year_dir, f"*{ymd}*.nc"),
        os.path.join(year_dir, f"{ymd}.nc"),
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(pat))
    return sorted(set(files))


def lon_to_180(lon: float) -> float:
    return ((lon + 180.0) % 360.0) - 180.0


def lon_to_360(lon: float) -> float:
    return lon % 360.0


def adapt_query_lon(lon_vals: np.ndarray, qlon: float) -> float:
    """If dataset longitudes are 0..360, convert query to 0..360; else to -180..180."""
    if np.nanmin(lon_vals) >= 0 and np.nanmax(lon_vals) > 180:
        return lon_to_360(qlon)
    else:
        return lon_to_180(qlon)


def nearest_index(arr: np.ndarray, value: float) -> int:
    """Return index of nearest value in 1D array (fast path for monotonic)."""
    try:
        if arr.ndim == 1 and np.all(np.diff(arr) >= 0):
            i = np.searchsorted(arr, value)
            if i == 0:
                return 0
            if i >= arr.size:
                return arr.size - 1
            return int(i if (abs(arr[i] - value) < abs(arr[i-1] - value)) else i-1)
        return int(np.argmin(np.abs(arr - value)))
    except Exception:
        return int(np.argmin(np.abs(arr - value)))


def compute_time_index(ds: xr.Dataset, when_np_day: np.datetime64):
    """Return time index to use (None if no time, 0 if single, nearest if multiple)."""
    sizes = getattr(ds, "sizes", None)
    if sizes is None:
        try:
            sizes = dict(ds.dims)
        except Exception:
            sizes = {}
    time_len = int(sizes.get(TIME_NAME, 0))
    if time_len <= 0:
        return None
    if time_len == 1:
        return 0
    tvals = ds[TIME_NAME].values
    return int(np.argmin(np.abs(tvals - when_np_day)))


def process_one_day(
    ds: xr.Dataset,
    rows: pd.DataFrame,
    var_names: List[str],
    tol_deg: float,
) -> Dict[int, Dict[str, float]]:
    """
    For one day's dataset ds, compute variable values for all rows.
    Returns {row_idx: {var: val}}.
    """
    results: Dict[int, Dict[str, float]] = {}

    lat_vals = ds[LAT_NAME].values
    lon_vals = ds[LON_NAME].values

    # Use first row's date (all rows in this group share the date)
    time_index = compute_time_index(ds, np.datetime64(rows.iloc[0]["_np_datetime"]))

    for ridx, r in rows.iterrows():
        lat = float(r[COL_LAT])
        lon = float(r[COL_LON])
        qlon = adapt_query_lon(lon_vals, lon)
        qlat = lat

        ilat = nearest_index(lat_vals, qlat)
        ilon = nearest_index(lon_vals, qlon)

        nearest_lat = float(lat_vals[ilat])
        nearest_lon = float(lon_vals[ilon])
        dlat = abs(nearest_lat - qlat)
        dlon = abs((((nearest_lon - qlon) + 180.0) % 360.0) - 180.0)

        res = {}
        if dlat > tol_deg or dlon > tol_deg:
            for v in var_names:
                res[v] = np.nan
            results[ridx] = res
            continue

        for v in var_names:
            if v not in ds.data_vars:
                res[v] = np.nan
                continue
            da = ds[v]
            indexer = {LAT_NAME: ilat, LON_NAME: ilon}
            if TIME_NAME in da.dims and time_index is not None:
                indexer[TIME_NAME] = time_index
            try:
                val = da.isel(**indexer).item()
                res[v] = float(val) if np.isfinite(val) else np.nan
            except Exception:
                res[v] = np.nan

        results[ridx] = res

    return results


# ----------------- MAIN -----------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract CHL, PFTs, and optics variables from plankton/optics NetCDF files."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input Excel or CSV file with sample dates and positions.",
    )
    parser.add_argument(
        "--plankton-base-dir",
        type=str,
        required=True,
        help="Base directory containing plankton NetCDF files (organized by year).",
    )
    parser.add_argument(
        "--optics-base-dir",
        type=str,
        required=False,
        help="Base directory containing optics NetCDF files (organized by year, optional).",
    )
    parser.add_argument(
        "--output-xlsx",
        type=str,
        required=False,
        help="Output Excel file path.",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        required=False,
        help="Output CSV file path.",
    )
    parser.add_argument(
        "--tol-deg",
        type=float,
        default=DEFAULT_TOL_DEG,
        help=f"Nearest neighbour tolerance in degrees (default: {DEFAULT_TOL_DEG}).",
    )
    parser.add_argument(
        "--year-col",
        type=str,
        default=COL_YEAR,
        help=f"Name of the 'year' column (default: {COL_YEAR}).",
    )
    parser.add_argument(
        "--month-col",
        type=str,
        default=COL_MONTH,
        help=f"Name of the 'month' column (default: {COL_MONTH}).",
    )
    parser.add_argument(
        "--day-col",
        type=str,
        default=COL_DAY,
        help=f"Name of the 'day' column (default: {COL_DAY}).",
    )
    parser.add_argument(
        "--lat-col",
        type=str,
        default=COL_LAT,
        help=f"Name of the latitude column (default: {COL_LAT}).",
    )
    parser.add_argument(
        "--lon-col",
        type=str,
        default=COL_LON,
        help=f"Name of the longitude column (default: {COL_LON}).",
    )
    parser.add_argument(
        "--plankton-vars",
        type=str,
        nargs="*",
        default=DEFAULT_PLANKTON_VARS,
        help="Variables to extract from plankton files (override defaults).",
    )
    parser.add_argument(
        "--optics-vars",
        type=str,
        nargs="*",
        default=DEFAULT_OPTICS_VARS,
        help="Variables to extract from optics files (override defaults).",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if not args.output_xlsx and not args.output_csv:
        raise SystemExit("You must specify at least one of --output-xlsx or --output-csv.")

    global COL_YEAR, COL_MONTH, COL_DAY, COL_LAT, COL_LON
    COL_YEAR = args.year_col
    COL_MONTH = args.month_col
    COL_DAY = args.day_col
    COL_LAT = args.lat_col
    COL_LON = args.lon_col

    plankton_base_dir = args.plankton_base_dir
    optics_base_dir = args.optics_base_dir

    # Read input (Excel or CSV)
    in_path = args.input
    if in_path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(in_path)
    else:
        df = pd.read_csv(in_path)

    # Check required columns
    required = [COL_YEAR, COL_MONTH, COL_DAY, COL_LAT, COL_LON]
    miss = [c for c in required if c not in df.columns]
    if miss:
        raise SystemExit(f"Missing columns in input table: {miss}")

    # Build date (no time) and daily precision timestamp
    df["_date"] = pd.to_datetime(
        dict(
            year=df[COL_YEAR].astype(int),
            month=df[COL_MONTH].astype(int),
            day=df[COL_DAY].astype(int),
        )
    )
    df["_np_datetime"] = df["_date"].dt.normalize().values.astype("datetime64[D]")

    # Prepare output columns for BOTH datasets
    # Plankton: keep names as-is (including 'flags')
    for v in args.plankton_vars:
        if v not in df.columns:
            df[v] = np.nan

    # Optics: rename 'flags' -> 'flags_optics' in the output
    for v in args.optics_vars:
        out_name = RENAME_OUT.get(("optics", v), v)
        if out_name not in df.columns:
            df[out_name] = np.nan

    # Group by date once
    grouped = df.groupby("_date", sort=True)
    total_groups = len(grouped)
    print(f"Processing {total_groups} distinct dates...")

    for gi, (day, rows) in enumerate(grouped, start=1):
        y, m, d = int(day.year), int(day.month), int(day.day)

        # -------- PLANKTON --------
        plank_candidates = file_candidates_for_date(plankton_base_dir, y, m, d)
        if plank_candidates:
            ds = None
            for path in plank_candidates:
                try:
                    ds = xr.open_dataset(path, engine="netcdf4", decode_times=True, mask_and_scale=True)
                    break
                except Exception:
                    continue
            if ds is not None:
                present_vars = [v for v in args.plankton_vars if v in ds.data_vars]
                missing = [v for v in args.plankton_vars if v not in ds.data_vars]
                if missing:
                    print(f"[{gi}/{total_groups}] {day.date()} (plankton): missing {missing}")
                day_results = process_one_day(ds, rows, present_vars, tol_deg=args.tol_deg)
                for ridx, values in day_results.items():
                    for v in args.plankton_vars:
                        df.at[ridx, v] = values.get(v, np.nan)
                try:
                    ds.close()
                except Exception:
                    pass
            else:
                print(f"[{gi}/{total_groups}] {day.date()} (plankton): could not open any candidate file")
        else:
            print(f"[{gi}/{total_groups}] {day.date()} (plankton): no file found")

        # -------- OPTICS --------
        if optics_base_dir:
            optics_candidates = file_candidates_for_date(optics_base_dir, y, m, d)
            if optics_candidates:
                ds = None
                for path in optics_candidates:
                    try:
                        ds = xr.open_dataset(path, engine="netcdf4", decode_times=True, mask_and_scale=True)
                        break
                    except Exception:
                        continue
                if ds is not None:
                    present_vars = [v for v in args.optics_vars if v in ds.data_vars]
                    missing = [v for v in args.optics_vars if v not in ds.data_vars]
                    if missing:
                        print(f"[{gi}/{total_groups}] {day.date()} (optics): missing {missing}")
                    day_results = process_one_day(ds, rows, present_vars, tol_deg=args.tol_deg)
                    for ridx, values in day_results.items():
                        for v in args.optics_vars:
                            out_name = RENAME_OUT.get(("optics", v), v)
                            df.at[ridx, out_name] = values.get(v, np.nan)
                    try:
                        ds.close()
                    except Exception:
                        pass
                else:
                    print(f"[{gi}/{total_groups}] {day.date()} (optics): could not open any candidate file")
            else:
                print(f"[{gi}/{total_groups}] {day.date()} (optics): no file found")

        print(f"[{gi}/{total_groups}] {day.date()}: done ({len(rows)} rows)")

    # Drop helper columns
    df.drop(columns=["_date", "_np_datetime"], inplace=True, errors="ignore")

    # Save outputs
    if args.output_xlsx:
        os.makedirs(os.path.dirname(args.output_xlsx), exist_ok=True)
        df.to_excel(args.output_xlsx, index=False)
        print(f"\nWrote Excel: {args.output_xlsx}")

    if args.output_csv:
        os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
        df.to_csv(args.output_csv, index=False)
        print(f"Wrote CSV:   {args.output_csv}")


if __name__ == "__main__":
    main()
