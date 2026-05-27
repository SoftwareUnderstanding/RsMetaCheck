from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Set, Union

import tomllib


DEFAULT_CONFIG_FILENAMES = (".rsmetacheck.toml", "rsmetacheck.toml")


@dataclass
class AnalysisConfig:
    ignored_checks: Set[str] = field(default_factory=set)
    exclude_files: list[str] = field(default_factory=list)
    check_parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    profile: Optional[str] = None
    source_path: Optional[Path] = None

    @classmethod
    def empty(cls) -> "AnalysisConfig":
        return cls()

    def is_ignored(self, check_code: str) -> bool:
        return _normalize_check_code(check_code) in self.ignored_checks

    def get_parameters(self, check_code: str) -> Dict[str, Any]:
        return self.check_parameters.get(_normalize_check_code(check_code), {})


def _normalize_check_code(value: str) -> str:
    return str(value).strip().upper()


def _normalize_check_codes(codes: Any) -> Set[str]:
    if not isinstance(codes, list):
        return set()
    normalized = set()
    for code in codes:
        if isinstance(code, str) and code.strip():
            normalized.add(_normalize_check_code(code))
    return normalized


def _normalize_exclude_files(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(v).strip() for v in values if isinstance(v, str) and str(v).strip()]


def _normalize_parameters(parameters: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(parameters, dict):
        return {}

    normalized: Dict[str, Dict[str, Any]] = {}
    for check_code, check_params in parameters.items():
        if not isinstance(check_code, str):
            continue
        if not isinstance(check_params, dict):
            continue
        normalized[_normalize_check_code(check_code)] = dict(check_params)
    return normalized


def _merge_parameters(
    base: Dict[str, Dict[str, Any]],
    override: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {k: dict(v) for k, v in base.items()}
    for check_code, params in override.items():
        merged.setdefault(check_code, {})
        merged[check_code].update(params)
    return merged


def _resolve_config_path(
    config_path: Optional[Union[str, Path]],
    cwd: Optional[Union[str, Path]] = None,
) -> Optional[Path]:
    if config_path:
        candidate = Path(config_path)
        if not candidate.exists():
            raise FileNotFoundError(f"Config file not found: {candidate}")
        return candidate

    search_root = Path(cwd) if cwd else Path.cwd()
    for filename in DEFAULT_CONFIG_FILENAMES:
        candidate = search_root / filename
        if candidate.exists():
            return candidate

    return None


def load_analysis_config(
    config_path: Optional[Union[str, Path]] = None,
    profile: Optional[str] = None,
    cwd: Optional[Union[str, Path]] = None,
) -> AnalysisConfig:
    """
    Load analysis configuration from TOML.

    Supported structure:

    ignore = ["P001", "W002"]
    exclude_files = ["**/codemeta.json"]

    [parameters.P001]
    ahead_significant_diff = 2

    [profiles.unstable]
    ignore = ["W002"]
    exclude_files = ["**/README.md"]

    [profiles.unstable.parameters.P001]
    ahead_significant_diff = 10
    """
    resolved_path = _resolve_config_path(config_path, cwd=cwd)
    if not resolved_path:
        return AnalysisConfig.empty()

    with resolved_path.open("rb") as f:
        raw = tomllib.load(f)

    selected_profile = profile or raw.get("active_profile")

    base_ignore = _normalize_check_codes(raw.get("ignore", []))
    base_exclude_files = _normalize_exclude_files(raw.get("exclude_files", []))
    base_parameters = _normalize_parameters(raw.get("parameters", {}))

    profile_ignore: Set[str] = set()
    profile_exclude_files: list[str] = []
    profile_parameters: Dict[str, Dict[str, Any]] = {}

    profiles = raw.get("profiles", {})
    if selected_profile:
        if not isinstance(profiles, dict) or selected_profile not in profiles:
            raise ValueError(f"Profile '{selected_profile}' was not found in {resolved_path}")

        selected = profiles[selected_profile]
        if not isinstance(selected, dict):
            raise ValueError(f"Profile '{selected_profile}' must be a TOML table")

        profile_ignore = _normalize_check_codes(selected.get("ignore", []))
        profile_exclude_files = _normalize_exclude_files(selected.get("exclude_files", []))
        profile_parameters = _normalize_parameters(selected.get("parameters", {}))

    merged_parameters = _merge_parameters(base_parameters, profile_parameters)

    return AnalysisConfig(
        ignored_checks=base_ignore | profile_ignore,
        exclude_files=base_exclude_files + profile_exclude_files,
        check_parameters=merged_parameters,
        profile=selected_profile,
        source_path=resolved_path,
    )
