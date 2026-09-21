from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.services.ai_service import generate_developer_report


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get("/weekly-activity")
def get_weekly_activity(
    username: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    today = date.today()

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    result = db.execute(
        text(
            """
            SELECT
                a.id,
                u.username,
                r.name AS repository,
                r.full_name,
                a.commit_sha,
                a.message,
                a.additions,
                a.deletions,
                a.changed_files,
                a.activity_url,
                a.occurred_at
            FROM activities a
            JOIN users u
                ON u.id = a.user_id
            JOIN repositories r
                ON r.id = a.repository_id
            WHERE u.username = :username
              AND a.occurred_at >= :week_start
              AND a.occurred_at < :week_end
            ORDER BY a.occurred_at DESC
            """
        ),
        {
            "username": username,
            "week_start": datetime.combine(
                week_start,
                datetime.min.time(),
            ),
            "week_end": datetime.combine(
                week_end + timedelta(days=1),
                datetime.min.time(),
            ),
        },
    )

    rows = result.mappings().all()

    return {
        "username": username,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "count": len(rows),
        "activities": [dict(row) for row in rows],
    }


@router.get("/stats")
def get_activity_stats(
    username: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    result = db.execute(
        text(
            """
            SELECT
                COUNT(*) AS total_commits,
                COUNT(DISTINCT a.repository_id) AS repositories_active,
                COALESCE(SUM(a.additions), 0) AS total_additions,
                COALESCE(SUM(a.deletions), 0) AS total_deletions
            FROM activities a
            JOIN users u
                ON u.id = a.user_id
            WHERE u.username = :username
            """
        ),
        {
            "username": username,
        },
    )

    row = result.mappings().one()

    return {
        "username": username,
        "total_commits": row["total_commits"],
        "repositories_active": row["repositories_active"],
        "total_additions": row["total_additions"],
        "total_deletions": row["total_deletions"],
    }


@router.post("/generate-ai")
async def generate_ai_report(
    username: str = Query(..., min_length=1),
    days: int = Query(default=30, ge=1, le=90),
    db: Session = Depends(get_db),
):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    result = db.execute(
        text(
            """
            SELECT
                r.name AS repository,
                r.full_name,
                a.commit_sha,
                a.message,
                a.additions,
                a.deletions,
                a.changed_files,
                a.activity_url,
                a.occurred_at
            FROM activities a
            JOIN users u
                ON u.id = a.user_id
            JOIN repositories r
                ON r.id = a.repository_id
            WHERE u.username = :username
              AND a.occurred_at >= :start_time
              AND a.occurred_at <= :end_time
            ORDER BY a.occurred_at DESC
            LIMIT 200
            """
        ),
        {
            "username": username,
            "start_time": start_time,
            "end_time": end_time,
        },
    )

    rows = result.mappings().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No GitHub activity found for {username} "
                f"in the last {days} days."
            ),
        )

    activities = [dict(row) for row in rows]

    latest_activity = rows[0]["occurred_at"]

    if hasattr(latest_activity, "date"):
        latest_date = latest_activity.date()
    else:
        latest_date = date.today()

    report_week_start = (
        latest_date
        - timedelta(days=latest_date.weekday())
    )

    report_week_end = report_week_start + timedelta(days=6)

    total_commits = len(rows)

    total_additions = sum(
        int(row["additions"] or 0)
        for row in rows
    )

    total_deletions = sum(
        int(row["deletions"] or 0)
        for row in rows
    )

    repositories_active = len(
        {
            row["full_name"]
            for row in rows
            if row["full_name"]
        }
    )

    ai_report = await generate_developer_report(
        username=username,
        activities=activities,
    )

    insert_result = db.execute(
        text(
            """
            INSERT INTO weekly_reports (
                user_id,
                week_start,
                week_end,
                total_commits,
                total_additions,
                total_deletions,
                repositories_active,
                projects_completed,
                productivity_score,
                summary,
                achievements,
                skills_improved,
                improvement_areas,
                recommendations,
                linkedin_draft
            )
            SELECT
                u.id,
                :week_start,
                :week_end,
                :total_commits,
                :total_additions,
                :total_deletions,
                :repositories_active,
                0,
                :productivity_score,
                :summary,
                CAST(:achievements AS JSONB),
                CAST(:skills_improved AS JSONB),
                CAST(:improvement_areas AS JSONB),
                CAST(:recommendations AS JSONB),
                :linkedin_draft
            FROM users u
            WHERE u.username = :username
            ON CONFLICT (user_id, week_start, week_end)
            DO UPDATE SET
                total_commits = EXCLUDED.total_commits,
                total_additions = EXCLUDED.total_additions,
                total_deletions = EXCLUDED.total_deletions,
                repositories_active = EXCLUDED.repositories_active,
                productivity_score = EXCLUDED.productivity_score,
                summary = EXCLUDED.summary,
                achievements = EXCLUDED.achievements,
                skills_improved = EXCLUDED.skills_improved,
                improvement_areas = EXCLUDED.improvement_areas,
                recommendations = EXCLUDED.recommendations,
                linkedin_draft = EXCLUDED.linkedin_draft
            RETURNING id;
            """
        ),
        {
            "username": username,
            "week_start": report_week_start,
            "week_end": report_week_end,
            "total_commits": total_commits,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "repositories_active": repositories_active,
            "productivity_score": ai_report["productivity_score"],
            "summary": ai_report["summary"],
            "achievements": __import__("json").dumps(
                ai_report["achievements"],
                ensure_ascii=False,
            ),
            "skills_improved": __import__("json").dumps(
                ai_report["skills_improved"],
                ensure_ascii=False,
            ),
            "improvement_areas": __import__("json").dumps(
                ai_report["improvement_areas"],
                ensure_ascii=False,
            ),
            "recommendations": __import__("json").dumps(
                ai_report["recommendations"],
                ensure_ascii=False,
            ),
            "linkedin_draft": ai_report["linkedin_draft"],
        },
    )

    saved_report = insert_result.fetchone()

    if not saved_report:
        db.rollback()

        raise HTTPException(
            status_code=404,
            detail=f"User {username} not found.",
        )

    db.commit()

    return {
        "success": True,
        "report_id": str(saved_report.id),
        "username": username,
        "analysis_window_days": days,
        "activity_count": total_commits,
        "week_start": report_week_start.isoformat(),
        "week_end": report_week_end.isoformat(),
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "repositories_active": repositories_active,
        "report": ai_report,
    }