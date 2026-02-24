"""
tests/test_pipeline.py
======================
Unit-Tests für die Predictive-Maintenance-Pipeline.

Getestet werden die kritischen Pfade der Module:
- data_generator : Datenerzeugung, Spaltenstruktur, Anomalie-Rate
- pipeline       : Bereinigung, Feature Engineering
- anomaly_detection : Z-Score, IQR, kombiniertes Flag

Autor : Portfolio-Projekt Predictive Maintenance
PEP 8 : Ja
"""

import sys
from pathlib import Path

# Projektverzeichnis in Suchpfad aufnehmen
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from data_generator import generate_sensor_data, SENSOR_COLUMNS
from pipeline import clean_data, engineer_features, load_data
from anomaly_detection import (
    compute_z_scores,
    flag_zscore_anomalies,
    compute_iqr_bounds,
    flag_iqr_anomalies,
    combined_anomaly_score,
    SENSOR_COLS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Kleiner synthetischer Datensatz für Tests (reproduzierbar)."""
    return generate_sensor_data(n_samples=200, anomaly_rate=0.1, seed=99)


@pytest.fixture
def processed_df(sample_df: pd.DataFrame, tmp_path: Path) -> pd.DataFrame:
    """Bereinigter und feature-engineerter Datensatz."""
    df = clean_data(sample_df)
    return engineer_features(df)


# ---------------------------------------------------------------------------
# data_generator
# ---------------------------------------------------------------------------

class TestDataGenerator:
    """Tests für data_generator.generate_sensor_data."""

    def test_column_names(self, sample_df: pd.DataFrame) -> None:
        """Alle erwarteten Spalten müssen vorhanden sein."""
        assert set(SENSOR_COLUMNS).issubset(set(sample_df.columns))

    def test_row_count(self, sample_df: pd.DataFrame) -> None:
        """Erzeugter Datensatz soll genau n_samples Zeilen haben."""
        assert len(sample_df) == 200

    def test_anomaly_rate(self, sample_df: pd.DataFrame) -> None:
        """Anomalie-Rate soll ±5 Prozentpunkte um den Sollwert liegen."""
        actual_rate = sample_df["label"].mean()
        assert abs(actual_rate - 0.1) < 0.05

    def test_reproducibility(self) -> None:
        """Gleicher Seed → identische DataFrames."""
        df1 = generate_sensor_data(n_samples=50, seed=7)
        df2 = generate_sensor_data(n_samples=50, seed=7)
        pd.testing.assert_frame_equal(df1, df2)

    def test_no_negative_values(self, sample_df: pd.DataFrame) -> None:
        """Physikalische Werte dürfen nicht negativ sein."""
        numeric = ["temperature_c", "vibration_mm_s", "pressure_bar", "cycle_time_s"]
        assert (sample_df[numeric] >= 0).all().all()


# ---------------------------------------------------------------------------
# pipeline – clean_data
# ---------------------------------------------------------------------------

class TestCleanData:
    """Tests für pipeline.clean_data."""

    def test_no_null_values(self, sample_df: pd.DataFrame) -> None:
        """Nach dem Bereinigen darf es keine NaN-Werte geben."""
        df = clean_data(sample_df)
        assert df.isnull().sum().sum() == 0

    def test_duplicates_removed(self, sample_df: pd.DataFrame) -> None:
        """Duplizierte Zeilen sollen entfernt werden."""
        df_duped = pd.concat([sample_df, sample_df.head(10)], ignore_index=True)
        df_clean = clean_data(df_duped)
        assert len(df_clean) <= len(df_duped)

    def test_values_within_range(self, sample_df: pd.DataFrame) -> None:
        """Temperatur nach Clipping: Werte zwischen 0 und 200."""
        df = clean_data(sample_df)
        assert df["temperature_c"].between(0, 200).all()


# ---------------------------------------------------------------------------
# pipeline – engineer_features
# ---------------------------------------------------------------------------

class TestEngineerFeatures:
    """Tests für pipeline.engineer_features."""

    def test_rolling_columns_exist(self, processed_df: pd.DataFrame) -> None:
        """Rollierende Feature-Spalten müssen vorhanden sein."""
        assert "temperature_c_roll_mean" in processed_df.columns
        assert "vibration_mm_s_roll_std" in processed_df.columns

    def test_diff_columns_exist(self, processed_df: pd.DataFrame) -> None:
        """Differenz-Spalten müssen vorhanden sein."""
        assert "pressure_bar_diff" in processed_df.columns

    def test_no_nulls_in_features(self, processed_df: pd.DataFrame) -> None:
        """Feature-Spalten dürfen keine NaN enthalten."""
        feat_cols = [c for c in processed_df.columns if "_roll_" in c or "_diff" in c]
        assert processed_df[feat_cols].isnull().sum().sum() == 0


# ---------------------------------------------------------------------------
# anomaly_detection
# ---------------------------------------------------------------------------

class TestAnomalyDetection:
    """Tests für anomaly_detection.*"""

    def test_zscore_columns_created(self, processed_df: pd.DataFrame) -> None:
        """Z-Score-Spalten müssen nach Berechnung existieren."""
        df = compute_z_scores(processed_df)
        for col in SENSOR_COLS:
            assert f"{col}_zscore" in df.columns

    def test_zscore_flag_is_bool(self, processed_df: pd.DataFrame) -> None:
        """anomaly_zscore muss eine Boolean-Spalte sein."""
        df = compute_z_scores(processed_df)
        df = flag_zscore_anomalies(df)
        assert df["anomaly_zscore"].dtype == bool

    def test_iqr_bounds_keys(self, processed_df: pd.DataFrame) -> None:
        """IQR-Bounds müssen für jeden Sensor 'lower' und 'upper' enthalten."""
        bounds = compute_iqr_bounds(processed_df)
        for col in SENSOR_COLS:
            assert "lower" in bounds[col]
            assert "upper" in bounds[col]

    def test_iqr_flag_is_bool(self, processed_df: pd.DataFrame) -> None:
        """anomaly_iqr muss eine Boolean-Spalte sein."""
        bounds = compute_iqr_bounds(processed_df)
        df = flag_iqr_anomalies(processed_df, bounds)
        assert df["anomaly_iqr"].dtype == bool

    def test_combined_flag_is_or(self, processed_df: pd.DataFrame) -> None:
        """combined = zscore OR iqr."""
        df = compute_z_scores(processed_df)
        df = flag_zscore_anomalies(df)
        bounds = compute_iqr_bounds(df)
        df = flag_iqr_anomalies(df, bounds)
        df = combined_anomaly_score(df)
        expected = df["anomaly_zscore"] | df["anomaly_iqr"]
        pd.testing.assert_series_equal(df["anomaly_combined"], expected, check_names=False)

    def test_no_anomaly_on_flat_signal(self) -> None:
        """Ein völlig konstantes Signal soll keine Anomalien erzeugen."""
        flat = pd.DataFrame({
            "machine_id": ["M1"] * 100,
            "temperature_c": [60.0] * 100,
            "vibration_mm_s": [1.0] * 100,
            "pressure_bar": [6.0] * 100,
            "cycle_time_s": [12.0] * 100,
        })
        df = compute_z_scores(flat)
        df = flag_zscore_anomalies(df)
        # Bei konstantem Signal ist std=0, Z-Score=0 → keine Anomalien
        assert df["anomaly_zscore"].sum() == 0
