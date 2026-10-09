"""
tools/data_access.py
Data loading / enrichment helpers used by the figure notebooks.

Ported from aind-vr-foraging-paper (aind_vr_foraging_analysis.utils.parsing.data_access
and supplementary_parsing.AddExtraColumns), trimmed to what the notebooks use.
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

warnings.filterwarnings("ignore", category=UserWarning)

_DEFAULT_STAGE_FILTER = ("data_collection", "base", "control")


# ---------------------------------------------------------------------------
# Per-session derived columns
# ---------------------------------------------------------------------------
class AddExtraColumns:
    """Add per-site / per-patch derived columns to a session's epochs table."""

    def __init__(self, all_epochs):
        self.all_epochs = all_epochs.copy()
        self.add_main_info()
        self.cumulative_consecutive()
        self.patch_time_entry()
        self.skipped_sites()

    def _replace_odor_sites(self, odor_sites):
        self.all_epochs = pd.concat(
            [self.all_epochs.loc[self.all_epochs.site_label != "RewardSite"], odor_sites],
            axis=0,
        ).sort_index()

    def add_main_info(self):
        odor_sites = self.all_epochs.loc[self.all_epochs.site_label == "RewardSite"].copy()

        odor_sites["odor_sites"] = np.arange(len(odor_sites))
        odor_sites["collected"] = odor_sites["has_reward"] * odor_sites["reward_amount"]
        odor_sites["depleted"] = np.where(odor_sites["reward_available"] == 0, 1, 0)

        next_site = odor_sites["site_index_in_patch_by_type"].shift(-2)
        odor_sites["last_visit"] = np.where(
            (next_site == 0) & (odor_sites["has_choice"] == True), 1, 0
        )

        last_site = odor_sites["site_index_in_patch_by_type"].shift(-1)
        odor_sites["last_site"] = np.where(last_site == 0, 1, 0)

        self._replace_odor_sites(odor_sites)

    def cumulative_consecutive(self):
        odor_sites = self.all_epochs.loc[self.all_epochs.site_label == "RewardSite"].copy()

        previous_patch = -1
        cumulative_rewards = 0
        consecutive_rewards = 0
        cumulative_failures = 0
        consecutive_failures = 0
        after_choice_cumulative_rewards = 0

        for index, row in odor_sites.iterrows():
            if row["patch_index"] != previous_patch:
                previous_patch = row["patch_index"]
                cumulative_rewards = 0
                cumulative_failures = 0
                consecutive_failures = 0
                consecutive_rewards = 0
                after_choice_cumulative_rewards = 0

            odor_sites.loc[index, "cumulative_rewards"] = cumulative_rewards
            odor_sites.loc[index, "consecutive_rewards"] = consecutive_rewards
            odor_sites.loc[index, "cumulative_failures"] = cumulative_failures
            odor_sites.loc[index, "consecutive_failures"] = consecutive_failures

            if row["has_reward"] != 0:
                cumulative_rewards += 1
                consecutive_rewards += 1
                consecutive_failures = 0
                after_choice_cumulative_rewards += 1

            odor_sites.loc[index, "after_choice_cumulative_rewards"] = (
                after_choice_cumulative_rewards
            )

            if row["has_reward"] == 0 and row["has_choice"] == True:
                cumulative_failures += 1
                consecutive_failures += 1
                consecutive_rewards = 0

        self._replace_odor_sites(odor_sites)

    def patch_time_entry(self):
        ep = self.all_epochs
        ep["duration_epoch"] = ep["stop_time"] - ep["start_time"]

        # Patch onset = start of the first InterSite epoch after a patch's first row
        onsets = {}
        patch_index = -1
        first_entry = True
        for _, row in ep.iterrows():
            if row["site_label"] == "InterSite" and patch_index == row["patch_index"] and first_entry:
                onsets[row["patch_index"]] = row["start_time"]
                first_entry = False
            if patch_index != row["patch_index"]:
                patch_index = row["patch_index"]
                first_entry = True
        patch_onset_map = pd.Series(onsets, dtype=float)

        ep["patch_onset"] = ep["patch_index"].map(patch_onset_map)
        ep["time_since_entry"] = ep["start_time"] - ep["patch_onset"]
        ep["exit_epoch"] = ep["time_since_entry"] + ep["duration_epoch"]

    def skipped_sites(self):
        odor_sites = self.all_epochs.loc[self.all_epochs.site_label == "RewardSite"].copy()

        skipped_count = 0
        for index, row in odor_sites.iterrows():
            # Consecutive skipped first sites - useful for filtering disengagement
            if row["has_choice"] == False and row["site_index_in_patch_by_type"] == 0:
                skipped_count += 1
            elif row["has_choice"] == True:
                skipped_count = 0
            odor_sites.loc[index, "skipped_count"] = skipped_count

        self._replace_odor_sites(odor_sites)


# ---------------------------------------------------------------------------
# Loading from S3
# ---------------------------------------------------------------------------
def load_session_catalogue_and_sites(
    s3_root: str,
    storage_options: dict,
    excluded_subjects: set[str],
):
    session_cat = (
        pl.scan_parquet(f"{s3_root}/session.parquet", storage_options=storage_options)
        .select("session_id", "subject_id", "date")
        .sort("date")
        .collect()
    )

    valid_session_ids = session_cat.filter(
        ~pl.col("subject_id").cast(pl.String).is_in([str(s) for s in excluded_subjects])
    )["session_id"]

    macro_df = (
        pl.scan_parquet(f"{s3_root}/sites.parquet", storage_options=storage_options)
        .filter(pl.col("session_id").is_in(valid_session_ids))
        .collect()
        .to_pandas()
    )

    return session_cat, valid_session_ids, macro_df


def get_s3_location(session_id: str, s3_root: str, storage_options: dict) -> str:
    result = (
        pl.scan_parquet(f"{s3_root}/session.parquet", storage_options=storage_options)
        .filter(pl.col("session_id") == session_id)
        .select("source_s3_location")
        .collect()
    )
    if result.is_empty():
        raise ValueError(f"session_id '{session_id}' not found")
    return result["source_s3_location"][0]


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------
def prepare_macro_df(
    macro_df: pd.DataFrame,
    stage_filter: tuple = _DEFAULT_STAGE_FILTER,
    stages_csv: str | Path = Path("results/sessions_stages.csv"),
    relabel_patches: bool = True,
) -> pd.DataFrame:
    """Merge stage names, relabel patch tiers, filter stages, add a mouse column."""
    join_col = "s_session" if "s_session" in macro_df.columns else "session_id"

    stages = pd.read_csv(stages_csv)
    macro_df = macro_df.merge(stages, left_on=join_col, right_on="session_id", how="left")

    macro_df["odor_concentration"] = macro_df["odor_concentration"].astype(str)

    if relabel_patches:
        def _safe_mode(s):
            s = s.dropna()
            return np.nan if s.empty else s.round(2).mode().iat[0]

        tier_lookup = (
            macro_df.loc[
                (macro_df.site_label == "RewardSite")
                & (macro_df.site_index_in_patch_by_type == 0)
            ]
            .groupby([join_col, "patch_label"])["reward_probability"]
            .agg(_safe_mode)
            .apply(lambda x: "90" if x > 0.75 else ("60" if x > 0.3 else "0"))
        )
        macro_df["patch_label"] = (
            macro_df.set_index([join_col, "patch_label"]).index.map(tier_lookup).values
        )

    macro_df = macro_df.loc[macro_df.stage_name.isin(stage_filter)]

    macro_df["mouse"] = macro_df.session_id.str.split("_").str[0]
    macro_df["mouse"] = np.where(
        macro_df["mouse"] == "behavior",
        macro_df.session_id.str.split("_").str[1],
        macro_df["mouse"],
    )

    return macro_df


def build_all_df(macro_df: pd.DataFrame) -> pd.DataFrame:
    """Apply AddExtraColumns per session and concatenate."""
    return pd.concat(
        [AddExtraColumns(group).all_epochs for _, group in macro_df.groupby("session_id")]
    )
