"""
UI_Data_Retrieval.py

Download wind data (eastward & northward wind components) from CMEMS via
the copernicusmarine Python client, for a list of points, to later compute
the Upwelling Index.

Examples
--------
Using a CSV with coordinates:

    python UI_Data_Retrieval.py \
        --output-dir "C:\\Data\\ui_wind" \
        --coords-file "C:\\Data\\stations.csv" \
        --lat-col LATITUDE \
        --lon-col LONGITUDE \
        --dataset-id "cmems_obs-wind_glo_phy_my_l4_0.125deg_PT1H" \
        --start "2013-01-01 00:00:00" \
        --end   "2023-12-31 23:00:00"

Using the built-in example coordinates:

    python UI_Data_Retrieval.py \
        --output-dir "C:\\Data\\ui_wind"
"""

import argparse
import os
from pathlib import Path

import copernicusmarine
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download CMEMS wind data for Upwelling Index computation."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where CSV files with wind data will be saved."
    )
    parser.add_argument(
        "--coords-file",
        type=str,
        default=None,
        help=(
            "Optional path to CSV file with coordinates. "
            "Must contain latitude/longitude columns (see --lat-col/--lon-col). "
            "If not given, built-in example coordinates are used."
        ),
    )
    parser.add_argument(
        "--lat-col",
        type=str,
        default="LATITUDE",
        help="Latitude column name in coords CSV (default: LATITUDE)."
    )
    parser.add_argument(
        "--lon-col",
        type=str,
        default="LONGITUDE",
        help="Longitude column name in coords CSV (default: LONGITUDE)."
    )
    parser.add_argument(
        "--id-col",
        type=str,
        default=None,
        help=(
            "Optional station ID column name in coords CSV. "
            "If provided, output files will be named using this ID."
        ),
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default="cmems_obs-wind_glo_phy_my_l4_0.125deg_PT1H",
        help="CMEMS wind dataset ID (default: cmems_obs-wind_glo_phy_my_l4_0.125deg_PT1H).",
    )
    parser.add_argument(
        "--variables",
        type=str,
        nargs="+",
        default=["eastward_wind", "northward_wind"],
        help="Variables to download (default: eastward_wind northward_wind).",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2013-01-01 00:00:00",
        help="Start datetime in 'YYYY-MM-DD HH:MM:SS' (dataset timezone).",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="2023-12-31 23:00:00",
        help="End datetime in 'YYYY-MM-DD HH:MM:SS' (dataset timezone).",
    )
    parser.add_argument(
        "--half-size",
        type=float,
        default=0.0625,
        help="Half-size (degrees) of the latitude/longitude box around each point.",
    )

    return parser.parse_args()


def load_coordinates(
    coords_file: Path | None,
    lat_col: str,
    lon_col: str,
    id_col: str | None,
) -> list[dict]:
    """
    Return a list of dicts with latitude, longitude and optional station_id.

    If coords_file is None, use internal example coordinates.
    """
    if coords_file is None:
        print("No coords file provided. Using built-in example coordinates.")
        example_coords = [
            {"latitude": 41.03335, "longitude": -8.701667, "station_id": "point_1"},
            {"latitude": 41.16944, "longitude": -8.71388, "station_id": "point_2"},
            {"latitude": 41.19662, "longitude": -8.711557, "station_id": "point_3"},
            {"latitude": 41.25367, "longitude": -8.769, "station_id": "point_4"},
            {"latitude": 41.27802, "longitude": -8.769, "station_id": "point_5"},
            {"latitude": 41.283333, "longitude": -8.894444, "station_id": "point_6"},
            {"latitude": 41.742833, "longitude": -8.878333, "station_id": "point_7"},
            {"latitude": 41.31111111, "longitude": -8.805555556, "station_id": "point_8"},
            {"latitude": 41.49221944, "longitude": -8.786027778, "station_id": "point_9"},
            {"latitude": 41.74916667, "longitude": -8.886111111, "station_id": "point_10"},
        ]
        return example_coords

    if not coords_file.exists():
        raise FileNotFoundError(f"Coordinates file not found: {coords_file}")

    df = pd.read_csv(coords_file)
    if lat_col not in df.columns or lon_col not in df.columns:
        raise ValueError(
            f"Latitude/longitude columns '{lat_col}', '{lon_col}' not found in {coords_file}"
        )

    coords_list: list[dict] = []
    for idx, row in df.iterrows():
        lat = float(row[lat_col])
        lon = float(row[lon_col])

        if id_col and id_col in df.columns:
            station_id = str(row[id_col])
        else:
            station_id = f"point_{idx + 1}"

        coords_list.append(
            {"latitude": lat, "longitude": lon, "station_id": station_id}
        )

    return coords_list


def main() -> None:
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    coords_file = Path(args.coords_file) if args.coords_file else None
    coords = load_coordinates(coords_file, args.lat_col, args.lon_col, args.id_col)

    print(f"Will download data for {len(coords)} point(s).")
    for i, c in enumerate(coords, start=1):
        lat = c["latitude"]
        lon = c["longitude"]
        station_id = c["station_id"]

        print(f"\nDownloading point {i} ({station_id}) at ({lat}, {lon})...")

        ds = copernicusmarine.open_dataset(
            dataset_id=args.dataset_id,
            minimum_latitude=lat - args.half_size,
            maximum_latitude=lat + args.half_size,
            minimum_longitude=lon - args.half_size,
            maximum_longitude=lon + args.half_size,
            start_datetime=args.start,
            end_datetime=args.end,
            variables=args.variables,
        )

        df = ds.to_dataframe().reset_index()

        # (Optional) harmonize column names
        if "latitude" not in df.columns and "lat" in df.columns:
            df["latitude"] = df["lat"]
        if "longitude" not in df.columns and "lon" in df.columns:
            df["longitude"] = df["lon"]

        df["latitude"] = lat
        df["longitude"] = lon
        df["station_id"] = station_id

        # Keep only what we need
        needed_cols = ["time"] + args.variables + ["latitude", "longitude", "station_id"]
        df = df[[col for col in needed_cols if col in df.columns]]

        csv_path = output_dir / f"wind_{station_id}.csv"
        df.to_csv(csv_path, index=False)
        print(f"Saved wind data to: {csv_path}")

    print("\nAll wind files downloaded.")


if __name__ == "__main__":
    main()
