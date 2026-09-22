from __future__ import annotations
class DatasetPublishError(Exception):
    """Base class for dataset publishing errors."""


class DatasetMetadataRetrievalError(DatasetPublishError):
    def __init__(self, survey_id: str, period_id: str, status_code: int) -> None:
        self.message = (
            f"Failed to retrieve metadata for dataset with survey_id: {survey_id} "
            f"and period_id: {period_id}, Status code: {status_code}"
        )
        super().__init__(self.message)


class DatasetCreateError(DatasetPublishError):
    def __init__(self, status_code: int) -> None:
        self.message = f"Failed to call the dataset/create endpoint. Status code: {status_code}"
        super().__init__(self.message)
