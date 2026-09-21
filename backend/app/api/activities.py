from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.activity import (
    ActivityIngestRequest,
    ActivityIngestResponse,
)


router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
)


@router.post(
    "/ingest",
    response_model=ActivityIngestResponse,
)
def ingest_activity(
    payload: ActivityIngestRequest,
    db: Session = Depends(get_db),
):
    try:
        # ------------------------------------------------------
        # 1. Create or find user
        # ------------------------------------------------------

        user_result = db.execute(
            text(
                """
                INSERT INTO users (
                    username,
                    email,
                    github_username
                )
                VALUES (
                    :username,
                    :email,
                    :github_username
                )
                ON CONFLICT (username)
                DO UPDATE SET
                    email = COALESCE(EXCLUDED.email, users.email),
                    github_username = COALESCE(
                        EXCLUDED.github_username,
                        users.github_username
                    ),
                    updated_at = NOW()
                RETURNING id, username;
                """
            ),
            {
                "username": payload.owner,
                "email": payload.author_email or None,
                "github_username": payload.owner,
            },
        )

        user = user_result.fetchone()

        if not user:
            raise HTTPException(
                status_code=500,
                detail="Unable to create or find user",
            )

        user_id = user.id
        username = user.username

        # ------------------------------------------------------
        # 2. Create or find repository
        # ------------------------------------------------------

        repo_result = db.execute(
            text(
                """
                INSERT INTO repositories (
                    user_id,
                    name,
                    full_name,
                    html_url,
                    updated_at
                )
                VALUES (
                    :user_id,
                    :name,
                    :full_name,
                    :html_url,
                    NOW()
                )
                ON CONFLICT (user_id, full_name)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    html_url = EXCLUDED.html_url,
                    updated_at = NOW()
                RETURNING id;
                """
            ),
            {
                "user_id": user_id,
                "name": payload.repository,
                "full_name": payload.full_repository,
                "html_url": payload.activity_url,
            },
        )

        repository = repo_result.fetchone()

        if not repository:
            raise HTTPException(
                status_code=500,
                detail="Unable to create or find repository",
            )

        repository_id = repository.id

        # ------------------------------------------------------
        # 3. Check whether this commit already exists
        # ------------------------------------------------------

        existing_result = db.execute(
            text(
                """
                SELECT id
                FROM activities
                WHERE repository_id = :repository_id
                  AND commit_sha = :commit_sha
                LIMIT 1;
                """
            ),
            {
                "repository_id": repository_id,
                "commit_sha": payload.commit_sha,
            },
        )

        existing_activity = existing_result.fetchone()

        # ------------------------------------------------------
        # 4. New activity → INSERT
        # ------------------------------------------------------

        if existing_activity is None:
            activity_result = db.execute(
                text(
                    """
                    INSERT INTO activities (
                        user_id,
                        repository_id,
                        activity_type,
                        commit_sha,
                        branch,
                        title,
                        message,
                        additions,
                        deletions,
                        changed_files,
                        activity_url,
                        occurred_at
                    )
                    VALUES (
                        :user_id,
                        :repository_id,
                        :activity_type,
                        :commit_sha,
                        NULL,
                        NULL,
                        :message,
                        :additions,
                        :deletions,
                        :changed_files,
                        :activity_url,
                        :occurred_at
                    )
                    RETURNING id;
                    """
                ),
                {
                    "user_id": user_id,
                    "repository_id": repository_id,
                    "activity_type": payload.activity_type,
                    "commit_sha": payload.commit_sha,
                    "message": payload.message,
                    "additions": payload.additions,
                    "deletions": payload.deletions,
                    "changed_files": payload.changed_files,
                    "activity_url": payload.activity_url,
                    "occurred_at": payload.date,
                },
            )

            activity = activity_result.fetchone()

            if not activity:
                raise HTTPException(
                    status_code=500,
                    detail="Unable to create activity",
                )

            is_new = True
            activity_id = activity.id

        # ------------------------------------------------------
        # 5. Existing activity → UPDATE
        # ------------------------------------------------------

        else:
            activity_id = existing_activity.id

            db.execute(
                text(
                    """
                    UPDATE activities
                    SET
                        message = :message,
                        additions = :additions,
                        deletions = :deletions,
                        changed_files = :changed_files,
                        activity_url = :activity_url,
                        occurred_at = :occurred_at
                    WHERE id = :activity_id;
                    """
                ),
                {
                    "activity_id": activity_id,
                    "message": payload.message,
                    "additions": payload.additions,
                    "deletions": payload.deletions,
                    "changed_files": payload.changed_files,
                    "activity_url": payload.activity_url,
                    "occurred_at": payload.date,
                },
            )

            is_new = False

        db.commit()

        return ActivityIngestResponse(
            success=True,
            is_new=is_new,
            activity_id=str(activity_id),
            repository_id=str(repository_id),
            username=username,
            message=(
                "New activity ingested successfully"
                if is_new
                else "Existing activity updated successfully"
            ),
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Activity ingestion failed: {str(exc)}",
        ) from exc