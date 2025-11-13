"""
UI_Data_Processing.py

Compute the Upwelling Index (UI) from wind data (eastward & northward wind
components), for one or more tables (CSV or Excel sheets).

The UI is computed following:

    tau_x = rho_air * Cd * |U| * u
    tau_y = rho_air * Cd * |U| * v
    f    = 2 * omega * sin(latitude)
    UI   = (tau_x * sin(theta) - tau_y * cos(theta)) / (rho_water * f)

where theta is the coastline angle (degrees from east).

Examples
--------
Single CSV:

    python UI_Data_Processing.py \
        --input "C:\\Data\\wind_point_1.csv" \
        --output "C:\\Data\\wind_point_1_ui.csv"

Excel with multiple sheets:

    python UI_Data_Processing.py \
        --input "C:\\Data\\wind_points.xlsx" \
        --output "C:\\Data\\wind_points_ui.xlsx" \
        --sheets Sheet1 Sheet2
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# === Default physical constants ===
RHO_AIR = 1.22       # kg/m³
RHO_WATER = 1025.0   # kg/m³
CD = 1.3e-3          # drag coefficient
OMEGA = 7.2921e-5    # rad/s (Earth rotation)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute Upwelling Index from wind data."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input file (CSV or Excel) containing wind data.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help=(
            "Path to output file. "
            "If extension is .xlsx/.xls -> Excel (multi-sheet if input is Excel). "
            "Otherwise -> CSV."
        ),
    )
    parser.add_argument(
        "--sheets",
        type=str,
        nargs="*",
        default=None,
        help=(
            "Optional list of sheet names to process (Excel only). "
            "If omitted and input is Excel, all sheets are processed."
        ),
    )
    parser.add_argument(
        "--date-col",
        type=str,
        default="Date",
        help="Name of the date column (default: Date).",
    )
    parser.add_argument(
        "--lat-col",
        type=str,
        default=None,
        help=(
            "Name of the latitude column. "
            "If not provided, script will look for 'LATITUDE' or 'latitude'."
        ),
    )
    parser.add_argument(
        "--u-col",
        type=str,
        default="eastward_wind",
        help="Name of the eastward wind component column (default: eastward_wind).",
    )
    parser.add_argument(
        "--v-col",
        type=str,
        default="northward_wind",
        help="Name of the northward wind component column (default: northward_wind).",
    )
    parser.add_argument(
        "--theta-deg",
        type=float,
        default=-32.0,
        help="Coastline angle in degrees from east (default: -32).",
    )

    return parser.parse_args()


def find_lat_column(df: pd.DataFrame, lat_col: str | None) -> str:
    """Return the name of the latitude column to use."""
    if lat_col and lat_col in df.columns:
        return lat_col
    if "LATITUDE" in df.columns:
        return "LATITUDE"
    if "latitude" in df.columns:
        return "latitude"
    raise ValueError("Could not find a latitude column (LATITUDE or latitude). Use --lat-col.")


def calculate_ui(
    df: pd.DataFrame,
    date_col: str,
    lat_col: str | None,
    u_col: str,
    v_col: str,
    theta_deg: float,
) -> pd.DataFrame:
    """
    Compute Upwelling Index for a DataFrame with wind data.

    Expects columns:
        - date_col: date/time string
        - lat_col: latitude in degrees
        - u_col: eastward wind component
        - v_col: northward wind component
    """
    df = df.copy()

    # Rename latitude column to a consistent internal name
    lat_name = find_lat_column(df, lat_col)
    df["latitude"] = df[lat_name]

    # Parse date/time (dayfirst=True for European DD/MM/YYYY style)
    df["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")

    # Compute Coriolis parameter f
    df["f"] = 2.0 * OMEGA * np.sin(np.radians(df["latitude"]))

    # Wind components
    u = df[u_col].astype(float)
    v = df[v_col].astype(float)
    wind_speed = np.sqrt(u**2 + v**2)

    # Wind stress
    df["tau_x"] = RHO_AIR * CD * wind_speed * u
    df["tau_y"] = RHO_AIR * CD * wind_speed * v

    # Coastline angle
    theta_rad = np.radians(theta_deg)
    sin_theta = np.sin(theta_rad)
    cos_theta = np.cos(theta_rad)

    # Upwelling Index (UI)
    # Avoid division by zero: where f is ~0, UI becomes NaN
    df["UI"] = np.where(
        np.abs(df["f"]) > 0,
        (df["tau_x"] * sin_theta - df["tau_y"] * cos_theta) / (RHO_WATER * df["f"]),
        np.nan,
    )

    # Optionally, drop internal columns
    df.drop(columns=["tau_x", "tau_y", "f"], inplace=True)

    return df


def process_file(
    input_path: Path,
    output_path: Path,
    sheets: list[str] | None,
    date_col: str,
    lat_col: str | None,
    u_col: str,
    v_col: str,
    theta_deg: float,
) -> None:
    """Process CSV or Excel, write CSV or Excel based on output extension."""
    ext_in = input_path.suffix.lower()
    ext_out = output_path.suffix.lower()

    if ext_in in [".xlsx", ".xls"]:
        # Excel input, possibly multiple sheets
        if sheets:
            sheet_dict = pd.read_excel(input_path, sheet_name=sheets)
        else:
            sheet_dict = pd.read_excel(input_path, sheet_name=None)  # all sheets

        out_dict: dict[str, pd.DataFrame] = {}
        for sheet_name, df in sheet_dict.items():
            print(f"Processing sheet: {sheet_name}")
            out_dict[sheet_name] = calculate_ui(
                df,
                date_col=date_col,
                lat_col=lat_col,
                u_col=u_col,
                v_col=v_col,
                theta_deg=theta_deg,
            )

        if ext_out in [".xlsx", ".xls"]:
            # Multi-sheet Excel output
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for name, df_out in out_dict.items():
                    df_out.to_excel(writer, sheet_name=name, index=False)
        else:
            # If output is not Excel, write first sheet to CSV
            first_sheet = next(iter(out_dict.keys()))
            out_df = out_dict[first_sheet]
            out_df.to_csv(output_path, index=False)

    else:
        # CSV input
        df = pd.read_csv(input_path)
        out_df = calculate_ui(
            df,
            date_col=date_col,
            lat_col=lat_col,
            u_col=u_col,
            v_col=v_col,
            theta_deg=theta_deg,
        )

        if ext_out in [".xlsx", ".xls"]:
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                out_df.to_excel(writer, index=False, sheet_name="Sheet1")
        else:
            out_df.to_csv(output_path, index=False)

    print(f"Upwelling Index added. Saved as: {output_path}")


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    process_file(
        input_path=input_path,
        output_path=output_path,
        sheets=args.sheets,
        date_col=args.date_col,
        lat_col=args.lat_col,
        u_col=args.u_col,
        v_col=args.v_col,
        theta_deg=args.theta_deg,
    )


if __name__ == "__main__":
    main()
