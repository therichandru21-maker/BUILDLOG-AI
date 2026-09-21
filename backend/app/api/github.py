from fastapi import APIRouter, HTTPException, Query

from app.services.github_service import (
    get_github_repositories,
    get_github_user,
    get_repository_commits,
)


router = APIRouter(
    prefix="/github",
    tags=["GitHub"],
)


@router.get("/profile/{username}")
async def github_profile(username: str):
    try:
        return await get_github_user(username)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub API request failed: {str(exc)}",
        ) from exc


@router.get("/repos/{username}")
async def github_repositories(
    username: str,
    limit: int = Query(default=10, ge=1, le=100),
):
    try:
        repositories = await get_github_repositories(
            username=username,
            per_page=limit,
        )

        return {
            "username": username,
            "count": len(repositories),
            "repositories": repositories,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub repository request failed: {str(exc)}",
        ) from exc


@router.get("/commits/{owner}/{repo}")
async def github_commits(
    owner: str,
    repo: str,
    author: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
):
    try:
        commits = await get_repository_commits(
            owner=owner,
            repo=repo,
            author=author,
            per_page=limit,
        )

        return {
            "repository": f"{owner}/{repo}",
            "count": len(commits),
            "commits": commits,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"GitHub commit request failed: {str(exc)}",
        ) from exc