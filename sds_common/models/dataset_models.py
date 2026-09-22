from __future__ import annotations
from dataclasses import dataclass


@dataclass
class DatasetMetadata:
    dataset_id: str
    survey_id: str
    period_id: str
    form_types: list[str]
    sds_published_at: str
    total_reporting_units: int
    sds_dataset_version: int
    filename: str
    title: str | None = None
