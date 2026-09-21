import httpx

from app.config import settings


GITHUB_API_BASE = "https://api.github.com"


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }

    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    return headers


async def get_github_user(username: str) -> dict:
    url = f"{GITHUB_API_BASE}/users/{username}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            url,
            headers=_headers(),
        )

    response.raise_for_status()
    data = response.json()

    return {
        "login": data.get("login"),
        "name": data.get("name"),
        "bio": data.get("bio"),
        "public_repos": data.get("public_repos", 0),
        "followers": data.get("followers", 0),
        "following": data.get("following", 0),
        "avatar_url": data.get("avatar_url"),
        "html_url": data.get("html_url"),
    }


async def get_github_repositories(
    username: str,
    per_page: int = 30,
) -> list[dict]:
    url = f"{GITHUB_API_BASE}/users/{username}/repos"

    params = {
        "sort": "updated",
        "direction": "desc",
        "per_page": min(per_page, 100),
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            url,
            params=params,
            headers=_headers(),
        )

    response.raise_for_status()
    repositories = response.json()

    return [
        {
            "github_id": repo.get("id"),
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "html_url": repo.get("html_url"),
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "is_private": repo.get("private", False),
        }
        for repo in repositories
    ]


async def get_repository_commits(
    owner: str,
    repo: str,
    author: str | None = None,
    per_page: int = 20,
) -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits"

    params = {
        "per_page": min(per_page, 100),
    }

    if author:
        params["author"] = author

    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            url,
            params=params,
            headers=_headers(),
        )

    response.raise_for_status()
    commits = response.json()

    result = []

    for commit in commits:
        commit_data = commit.get("commit", {})
        author_data = commit_data.get("author") or {}
        stats = commit.get("stats") or {}

        result.append(
            {
                "sha": commit.get("sha"),
                "message": commit_data.get("message"),
                "author_name": author_data.get("name"),
                "author_email": author_data.get("email"),
                "date": author_data.get("date"),
                "url": commit.get("html_url"),
                "additions": stats.get("additions", 0),
                "deletions": stats.get("deletions", 0),
                "changed_files": stats.get("total", 0),
            }
        )

    return result