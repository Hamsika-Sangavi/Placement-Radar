"""Reusable analysis functions used by the dashboard, the exports and the tests."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def load_tables(path: Path = PROCESSED) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    jobs = pd.read_csv(path / "jobs.csv", parse_dates=["posted_at"])
    skills = pd.read_csv(path / "job_skills.csv")
    cities = pd.read_csv(path / "job_cities.csv")
    return jobs, skills, cities


def filter_jobs(
    jobs: pd.DataFrame,
    cities: pd.DataFrame,
    roles: list[str] | None = None,
    city: str | None = None,
    exp_bands: list[str] | None = None,
) -> pd.DataFrame:
    """Filter jobs by role family, city (multi-city postings count in each city) and experience band."""
    out = jobs
    if roles:
        out = out[out["role_family"].isin(roles)]
    if city and city != "All cities":
        ids = cities.loc[cities["city"] == city, "job_id"]
        out = out[out["job_id"].isin(ids)]
    if exp_bands:
        out = out[out["exp_band"].isin(exp_bands)]
    return out


def skill_demand(skills: pd.DataFrame, job_ids: pd.Series | pd.Index, top: int | None = None) -> pd.DataFrame:
    """Share of the given jobs that mention each skill."""
    ids = set(job_ids)
    n = len(ids)
    sub = skills[skills["job_id"].isin(ids)]
    out = (
        sub.groupby(["skill", "skill_category"]).size().rename("jobs").reset_index()
        .sort_values("jobs", ascending=False)
    )
    out["share"] = out["jobs"] / max(n, 1)
    return out.head(top) if top else out


def skill_by_role(jobs: pd.DataFrame, skills: pd.DataFrame, top_skills: int = 15) -> pd.DataFrame:
    """Matrix of skill share by role family (for the heatmap)."""
    keep = skills["skill"].value_counts().head(top_skills).index
    base = jobs.groupby("role_family").size().rename("n")
    m = (
        skills[skills["skill"].isin(keep)]
        .merge(jobs[["job_id", "role_family"]], on="job_id")
        .groupby(["role_family", "skill"]).size().rename("jobs").reset_index()
        .merge(base, on="role_family")
    )
    m["share"] = m["jobs"] / m["n"]
    return m


def city_summary(jobs: pd.DataFrame, cities: pd.DataFrame, min_jobs: int = 100) -> pd.DataFrame:
    """Per city: postings, fresher-friendly share, median experience, share with disclosed salary."""
    m = cities.merge(jobs, on="job_id")
    g = m.groupby("city")
    out = pd.DataFrame(
        {
            "jobs": g.size(),
            "fresher_share": g["is_fresher_friendly"].mean(),
            "median_exp_min": g["exp_min"].median(),
            "median_salary_lpa": g["salary_mid_lpa"].median(),
            "salary_disclosed": g["has_salary"].sum(),
        }
    ).reset_index()
    return out[out["jobs"] >= min_jobs].sort_values("jobs", ascending=False)


def company_summary(jobs: pd.DataFrame, min_jobs: int = 25) -> pd.DataFrame:
    """Top hiring companies with their employee rating (from AmbitionBox)."""
    g = jobs.groupby("company")
    out = pd.DataFrame(
        {
            "jobs": g.size(),
            "rating": g["company_rating"].mean(),
            "fresher_share": g["is_fresher_friendly"].mean(),
            "top_role": g["role_family"].agg(lambda s: s.value_counts().index[0]),
        }
    ).reset_index()
    return out[out["jobs"] >= min_jobs].sort_values("jobs", ascending=False)


# ------------------------------------------------------------ skill gap


def job_skill_sets(skills: pd.DataFrame, job_ids) -> dict[int, set[str]]:
    sub = skills[skills["job_id"].isin(set(job_ids))]
    return sub.groupby("job_id")["skill"].agg(set).to_dict()


def gap_report(
    user_skills: list[str],
    jobs: pd.DataFrame,
    skills: pd.DataFrame,
    ready_threshold: float = 0.6,
    min_skills_in_job: int = 3,
    suggestions: int = 6,
) -> dict:
    """Compare a person's skills with a set of jobs.

    For each job: match = share of the job's skills the person already has.
    A job counts as "ready" when match >= ready_threshold. Jobs that list fewer than
    `min_skills_in_job` skills are ignored because a match score on 1-2 skills is noise.

    For each missing skill, `unlocks` = how many more jobs become "ready" if it is added
    (marginal gain, computed against the current skill set).
    """
    mine = {s for s in user_skills}
    sets = {jid: s for jid, s in job_skill_sets(skills, jobs["job_id"]).items() if len(s) >= min_skills_in_job}
    n_jobs = len(sets)
    if n_jobs == 0:
        return {"n_jobs": 0, "ready": 0, "ready_share": 0.0, "avg_match": 0.0, "suggestions": pd.DataFrame()}

    def ready_count(have: set[str]) -> int:
        return sum(1 for s in sets.values() if len(s & have) / len(s) >= ready_threshold)

    matches = [len(s & mine) / len(s) for s in sets.values()]
    base_ready = ready_count(mine)

    candidates = {sk for s in sets.values() for sk in s} - mine
    rows = []
    for sk in candidates:
        gain = ready_count(mine | {sk}) - base_ready
        demand = sum(1 for s in sets.values() if sk in s) / n_jobs
        rows.append((sk, gain, demand))
    sug = (
        pd.DataFrame(rows, columns=["skill", "unlocks", "demand"])
        .sort_values(["unlocks", "demand"], ascending=False)
        .head(suggestions)
        .reset_index(drop=True)
    )
    return {
        "n_jobs": n_jobs,
        "ready": base_ready,
        "ready_share": base_ready / n_jobs,
        "avg_match": sum(matches) / n_jobs,
        "suggestions": sug,
    }


def best_matches(user_skills: list[str], jobs: pd.DataFrame, skills: pd.DataFrame, top: int = 15) -> pd.DataFrame:
    """Jobs ranked by how much of their skill list the person already has."""
    mine = set(user_skills)
    sets = job_skill_sets(skills, jobs["job_id"])
    rows = []
    for jid, s in sets.items():
        if len(s) < 3:
            continue
        have = s & mine
        rows.append((jid, len(have) / len(s), ", ".join(sorted(s - mine))))
    m = pd.DataFrame(rows, columns=["job_id", "match", "missing_skills"])
    out = m.merge(jobs[["job_id", "title", "company", "location_raw", "exp_min", "exp_max", "company_rating", "job_url"]], on="job_id")
    return out.sort_values(["match", "company_rating"], ascending=False).head(top)
