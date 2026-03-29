"""
signal_design_custom_brandon.py - Custom signal design project

Author: Brandon D. Smith
Date: 2026-03

Alcohol Consumption Data

- Data is taken from a state-level alcohol consumption dataset.
- Each row represents one state in one year.

Purpose

- Read alcohol consumption data from a CSV file.
- Design useful signals using beer and spirits.
- Save the resulting signals as a new CSV artifact.
- Create a chart visualization (JPG).

Paths (relative to repo root)

    INPUT FILE: data/niaaa_apparent_per_capita_consumption_1977_2023.csv
    OUTPUT FILE: artifacts/signals_consumption.csv

Run with:

    uv run python -m cintel.signal_design_custom_brandon
"""

# === DECLARE IMPORTS (packages we will use in this project) ===

import logging
from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
import polars as pl
from datafun_toolkit.logger import get_logger, log_header, log_path

# === CONFIGURE LOGGER ONCE PER MODULE (FILE) ===

LOG: logging.Logger = get_logger("P3", level="DEBUG")

# === DECLARE GLOBAL CONSTANTS FOR FOLDER PATHS (directories) ===

ROOT_DIR: Final[Path] = Path.cwd()
DATA_DIR: Final[Path] = ROOT_DIR / "data"
ARTIFACTS_DIR: Final[Path] = ROOT_DIR / "artifacts"

# === DECLARE GLOBAL CONSTANTS FOR FILE PATHS ===

DATA_FILE: Final[Path] = (
    DATA_DIR / "niaaa_apparent_per_capita_consumption_1977_2023.csv"
)
OUTPUT_FILE: Final[Path] = ARTIFACTS_DIR / "signals_consumption.csv"
CHART_FILE: Final[Path] = ARTIFACTS_DIR / "consumption_chart.jpg"


# === DEFINE THE MAIN FUNCTION ===


def main() -> None:
    """Run the pipeline.

    log_header() logs a standard run header.
    log_path() logs repo-relative paths (privacy-safe).
    """
    log_header(LOG, "CINTEL")

    LOG.info("========================")
    LOG.info("START main()")
    LOG.info("========================")

    # Log the constants to help with debugging and transparency.
    log_path(LOG, "ROOT_DIR", ROOT_DIR)
    log_path(LOG, "DATA_FILE", DATA_FILE)
    log_path(LOG, "OUTPUT_FILE", OUTPUT_FILE)
    log_path(LOG, "CHART_FILE", CHART_FILE)

    # Ensure output folders exist.
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    log_path(LOG, "ARTIFACTS_DIR", ARTIFACTS_DIR)

    # ----------------------------------------------------
    # STEP 1: READ CSV DATA FILE INTO A POLARS DATAFRAME
    # ----------------------------------------------------
    df: pl.DataFrame = pl.read_csv(DATA_FILE)

    LOG.info(f"Loaded {df.height} alcohol consumption records")

    # ----------------------------------------------------
    # STEP 2: DESIGN SIGNALS FROM RAW METRICS
    # ----------------------------------------------------
    LOG.info("Designing signals from the raw metrics...")

    # ----------------------------------------------------
    # STEP 2.1: DEFINE A CONDITION WE CAN REUSE
    # ----------------------------------------------------
    # Only calculate share signals when total alcohol is positive.
    is_total_positive: pl.Expr = pl.col("ethanol_all_drinks_gallons_per_capita") > 0

    # ----------------------------------------------------
    # STEP 2.2: DEFINE THE BEER SHARE CALCULATION
    # ----------------------------------------------------
    calculated_beer_share: pl.Expr = pl.col("ethanol_beer_gallons_per_capita") / pl.col(
        "ethanol_all_drinks_gallons_per_capita"
    )

    # ----------------------------------------------------
    # STEP 2.3: DEFINE THE BEER SHARE SIGNAL RECIPE
    # ----------------------------------------------------
    beer_share_signal_recipe: pl.Expr = (
        pl.when(is_total_positive)
        .then(calculated_beer_share)
        .otherwise(0.0)
        .alias("beer_share_signal")
    )

    # ----------------------------------------------------
    # STEP 2.4: DEFINE THE SPIRIT SHARE CALCULATION
    # ----------------------------------------------------
    calculated_spirit_share: pl.Expr = pl.col(
        "ethanol_spirit_gallons_per_capita"
    ) / pl.col("ethanol_all_drinks_gallons_per_capita")

    # ----------------------------------------------------
    # STEP 2.5: DEFINE THE SPIRIT SHARE SIGNAL RECIPE
    # ----------------------------------------------------
    spirit_share_signal_recipe: pl.Expr = (
        pl.when(is_total_positive)
        .then(calculated_spirit_share)
        .otherwise(0.0)
        .alias("spirit_share_signal")
    )

    # ----------------------------------------------------
    # STEP 2.6: DEFINE THE TOTAL SELECTED SIGNAL RECIPE
    # ----------------------------------------------------
    # This combines beer and spirits into one simple total signal.
    total_selected_signal_recipe: pl.Expr = (
        pl.col("ethanol_beer_gallons_per_capita")
        + pl.col("ethanol_spirit_gallons_per_capita")
    ).alias("total_selected_signal")

    # ----------------------------------------------------
    # STEP 2.7: DEFINE A SIMPLE DRINK COUNT SIGNAL RECIPE
    # ----------------------------------------------------
    # This keeps a very understandable signal for charting and reporting.
    total_drinks_signal_recipe: pl.Expr = pl.col("number_of_drinks_total").alias(
        "total_drinks_signal"
    )

    # ----------------------------------------------------
    # STEP 2.8: APPLY THE SIGNAL RECIPES TO THE DATAFRAME
    # ----------------------------------------------------
    df_with_signals: pl.DataFrame = df.with_columns(
        [
            beer_share_signal_recipe,
            spirit_share_signal_recipe,
            total_selected_signal_recipe,
            total_drinks_signal_recipe,
        ]
    )

    LOG.info(
        "Created signal columns: "
        "beer_share_signal, spirit_share_signal, "
        "total_selected_signal, total_drinks_signal"
    )

    # ----------------------------------------------------
    # STEP 3: SELECT THE COLUMNS WE WANT TO SAVE
    # ----------------------------------------------------
    signals_df: pl.DataFrame = df_with_signals.select(
        [
            "state_name",
            "year",
            "ethanol_beer_gallons_per_capita",
            "ethanol_spirit_gallons_per_capita",
            "ethanol_all_drinks_gallons_per_capita",
            "number_of_beers",
            "number_of_shots_liquor",
            "number_of_drinks_total",
            "beer_share_signal",
            "spirit_share_signal",
            "total_selected_signal",
            "total_drinks_signal",
        ]
    )

    LOG.info(f"Enhanced signals table has {signals_df.height} rows")

    # ----------------------------------------------------
    # STEP 4: SAVE THE SIGNALS TABLE AS AN ARTIFACT
    # ----------------------------------------------------
    signals_df.write_csv(OUTPUT_FILE)
    LOG.info(f"Wrote signals file: {OUTPUT_FILE}")

    # ----------------------------------------------------
    # STEP 5: CREATE CLEAR + MODERN CHART (JPG)
    # ----------------------------------------------------
    LOG.info("Creating visualization chart...")

    chart_df: pl.DataFrame = (
        df_with_signals.group_by("year")
        .agg(
            [
                pl.col("number_of_beers").mean().alias("avg_beers"),
                pl.col("number_of_shots_liquor").mean().alias("avg_shots"),
            ]
        )
        .sort("year")
    )

    # Modern style
    plt.style.use("dark_background")

    plt.figure(figsize=(12, 6))

    # Plot lines
    plt.plot(
        chart_df["year"],
        chart_df["avg_beers"],
        linewidth=3,
        label="Beer",
    )

    plt.plot(
        chart_df["year"],
        chart_df["avg_shots"],
        linewidth=3,
        label="Spirits",
    )

    # Fill for visual effect
    plt.fill_between(
        chart_df["year"],
        chart_df["avg_beers"],
        alpha=0.2,
    )

    plt.fill_between(
        chart_df["year"],
        chart_df["avg_shots"],
        alpha=0.2,
    )

    # CLEAR labels (this fixes your confusion issue)
    plt.title("Average Alcohol Consumption Over Time", fontsize=16)
    plt.xlabel("Year", fontsize=12)
    plt.ylabel("Average Number of Drinks per Person Each Year", fontsize=12)

    # Cleaner axis
    plt.xticks(chart_df["year"][::5])

    plt.legend(title="Drink Type")
    plt.grid(alpha=0.2)

    plt.tight_layout()

    # ✅ SAVE TO ARTIFACTS FOLDER
    chart_path: Path = ARTIFACTS_DIR / "consumption_chart.jpg"
    plt.savefig(chart_path, dpi=300, bbox_inches="tight")
    plt.close()

    LOG.info(f"Saved chart file: {CHART_FILE}")

    LOG.info("========================")
    LOG.info("Pipeline executed successfully!")
    LOG.info("========================")
    LOG.info("END main()")


# === CONDITIONAL EXECUTION GUARD ===

if __name__ == "__main__":
    main()
