from datetime import datetime

from pydantic import BaseModel, Field


class ActivityIngestRequest(BaseModel):
    owner: str = Field(min_length=1)
    repository: str = Field(min_length=1)
    full_repository: str = Field(min_length=1)

    commit_sha: str = Field(min_length=1)
    message: str = ""

    author_name: str = ""
    author_email: str = ""

    date: datetime

    activity_url: str = ""

    additions: int = 0
    deletions: int = 0
    changed_files: int = 0

    activity_type: str = "commit"


class ActivityIngestResponse(BaseModel):
    success: bool
    is_new: bool
    activity_id: str
    repository_id: str
    username: str
    message: str