"""Shared helper functions for the figure notebooks and scripts."""
from pathlib import Path


def repo_root() -> Path:
    """Repo root (the directory containing pyproject.toml)."""
    return Path(__file__).resolve().parents[2]


def panels_dir(fig_name: str) -> Path:
    """Output folder for a figure's panels, e.g. panels_dir("fig1"); created if missing."""
    path = repo_root() / "figures" / fig_name / "panels"
    path.mkdir(parents=True, exist_ok=True)
    return path
