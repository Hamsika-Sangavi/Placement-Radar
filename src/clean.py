"""Clean the raw Naukri export into analysis-ready tables.

Run:  python -m src.clean
Reads  data/raw/naukri_data_scientist.csv
Writes data/processed/*.csv and data/placement_radar.db (SQLite)
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.skills import SKILL_CATEGORY, clean_text, extract_skills

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "naukri_data_scientist.csv"
PROCESSED = ROOT / "data" / "processed"
DB_PATH = ROOT / "data" / "placement_radar.db"

# ---------------------------------------------------------------- parsers


def parse_experience(text) -> tuple[float, float]:
    """'3-8 Yrs' -> (3, 8); '5 Yrs' -> (5, 5); anything else -> (nan, nan)."""
    if not isinstance(text, str):
        return (np.nan, np.nan)
    m = re.search(r"(\d+)\s*-\s*(\d+)", text)
    if m:
        return (float(m.group(1)), float(m.group(2)))
    m = re.search(r"(\d+)", text)
    if m:
        return (float(m.group(1)), float(m.group(1)))
    return (np.nan, np.nan)


def parse_salary_lpa(text) -> tuple[float, float]:
    """'10-20 Lacs PA' -> (10, 20) in lakh per annum. Undisclosed or odd formats -> nan."""
    if not isinstance(text, str) or "lacs" not in text.lower():
        return (np.nan, np.nan)
    m = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", text)
    if not m:
        return (np.nan, np.nan)
    lo, hi = float(m.group(1)), float(m.group(2))
    return (lo, hi) if lo <= hi else (hi, lo)


def experience_band(exp_min) -> str:
    if pd.isna(exp_min):
        return "Unknown"
    if exp_min <= 1:
        return "Fresher (0-1 yrs)"
    if exp_min <= 3:
        return "Junior (2-3 yrs)"
    if exp_min <= 6:
        return "Mid (4-6 yrs)"
    return "Senior (7+ yrs)"


CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bangalore/bengaluru": "Bengaluru",
    "secunderabad": "Hyderabad",
    "hyderabad/secunderabad": "Hyderabad",
    "hyderabad": "Hyderabad",
    "gurugram": "Gurgaon",
    "gurgaon": "Gurgaon",
    "gurugram/gurgaon": "Gurgaon",
    "new delhi": "Delhi",
    "delhi / ncr": "Delhi",
    "delhi/ncr": "Delhi",
    "delhi ncr": "Delhi",
    "navi mumbai": "Mumbai",
    "mumbai suburbs": "Mumbai",
    "mumbai (all areas)": "Mumbai",
    "greater noida": "Noida",
    "pune": "Pune",
    "chennai": "Chennai",
    "kolkata": "Kolkata",
    "noida": "Noida",
    "mumbai": "Mumbai",
    "delhi": "Delhi",
    "ahmedabad": "Ahmedabad",
    "jaipur": "Jaipur",
    "kochi": "Kochi",
    "coimbatore": "Coimbatore",
    "chandigarh": "Chandigarh",
    "indore": "Indore",
}

IGNORE_TOKENS = {"hybrid", "remote", "work from home", "wfh", "temporary", "pan india", "india", "all areas"}


def parse_locations(text) -> tuple[list[str], bool]:
    """Return (list of clean cities, is_remote). Handles multi-city postings."""
    if not isinstance(text, str):
        return ([], False)
    low = text.lower()
    is_remote = "remote" in low or "work from home" in low or "wfh" in low
    cities: list[str] = []
    for tok in re.split(r"[,;]", text):
        tok = re.sub(r"\(.*?\)", "", tok)  # drop "(All Areas)" and similar
        tok = re.sub(r"^(hybrid|remote)\s*-\s*", "", tok.strip(), flags=re.I).strip()
        key = tok.lower()
        if not key or key in IGNORE_TOKENS:
            continue
        city = CITY_ALIASES.get(key, tok.title())
        if city not in cities:
            cities.append(city)
    return (cities, is_remote)


ROLE_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("ML / AI Engineer", ("machine learning", "ml engineer", "ai engineer", "genai", "gen ai", "nlp", "llm",
                          "deep learning", "computer vision", "artificial intelligence", "ai/ml", "ai ml")),
    ("Data Scientist", ("data scientist", "data science", "scientist")),
    ("Data Engineer", ("data engineer", "etl", "big data", "data platform", "databricks", "snowflake",
                       "pyspark", "data architect", "data warehouse", "dataops")),
    ("BI / Reporting", ("power bi", "tableau", "bi developer", "bi engineer", "business intelligence",
                        "reporting", "bi analyst", "dashboard")),
    ("Business Analyst", ("business analyst", "product analyst", "business analysis")),
    ("Data Analyst", ("data analyst", "analytics", "analyst")),
    ("Software Developer", ("developer", "software", "sde", "full stack", "fullstack", "backend",
                            "back end", "programmer", "java", "python", "application")),
]


def role_family(title) -> str:
    if not isinstance(title, str):
        return "Other"
    low = title.lower()
    for family, keys in ROLE_RULES:
        if any(k in low for k in keys):
            return family
    return "Other"


# ---------------------------------------------------------------- pipeline


def build_tables(raw_path: Path = RAW) -> dict[str, pd.DataFrame]:
    df = pd.read_csv(raw_path)
    rows_raw = len(df)
    df = df.drop_duplicates(subset="jobId").copy()

    exp = df["experience"].apply(parse_experience)
    sal = df["salary"].apply(parse_salary_lpa)
    loc = df["location"].apply(parse_locations)
    created = pd.to_datetime(df["createdDate"], errors="coerce")
    created = created.where(created > "2000-01-01")  # 1970-01-01 is a placeholder

    jobs = pd.DataFrame(
        {
            "job_id": df["jobId"].astype("int64"),
            "title": df["title"].str.strip(),
            "role_family": df["title"].apply(role_family),
            "company": df["companyName"].str.strip(),
            "exp_min": exp.str[0],
            "exp_max": exp.str[1],
            "salary_min_lpa": sal.str[0],
            "salary_max_lpa": sal.str[1],
            "location_raw": df["location"],
            "n_cities": loc.str[0].str.len(),
            "is_remote": loc.str[1],
            "posted_at": created,
            "company_rating": df["ambitionBoxData/AggregateRating"],
            "company_reviews": df["ambitionBoxData/ReviewsCount"],
            "vacancies": df["vacancy"],
            "source_mode": df["mode"],
            "job_url": df["jdURL"],
        }
    )
    jobs["exp_band"] = jobs["exp_min"].apply(experience_band)
    jobs["is_fresher_friendly"] = jobs["exp_min"] <= 1
    jobs["has_salary"] = jobs["salary_min_lpa"].notna()
    jobs["salary_mid_lpa"] = (jobs["salary_min_lpa"] + jobs["salary_max_lpa"]) / 2

    # ---- skills
    desc = df["jobDescription"].apply(clean_text)
    skills = [
        extract_skills(t, tags, d)
        for t, tags, d in zip(df["title"], df["tagsAndSkills"], desc)
    ]
    jobs["n_skills"] = [len(s) for s in skills]
    job_skills = pd.DataFrame(
        [(jid, sk) for jid, lst in zip(jobs["job_id"], skills) for sk in lst],
        columns=["job_id", "skill"],
    )
    job_skills["skill_category"] = job_skills["skill"].map(SKILL_CATEGORY)

    # ---- cities (one row per job per city)
    city_rows = []
    for jid, (cities, _) in zip(jobs["job_id"], loc):
        for c in cities:
            city_rows.append((jid, c))
    job_cities = pd.DataFrame(city_rows, columns=["job_id", "city"])

    # Keep a job-level primary city for single-city charts
    first_city = {jid: (c[0][0] if c[0] else None) for jid, c in zip(jobs["job_id"], loc)}
    jobs["primary_city"] = jobs["job_id"].map(first_city)
    jobs["in_hyderabad"] = jobs["job_id"].isin(job_cities.loc[job_cities.city == "Hyderabad", "job_id"])

    jobs.attrs["rows_raw"] = rows_raw
    return {"jobs": jobs, "job_skills": job_skills, "job_cities": job_cities}


def write_outputs(tables: dict[str, pd.DataFrame]) -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, t in tables.items():
        t.to_csv(PROCESSED / f"{name}.csv", index=False)
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as con:
        for name, t in tables.items():
            t.to_sql(name, con, index=False)
        con.executescript(
            "CREATE INDEX idx_js_job ON job_skills(job_id);"
            "CREATE INDEX idx_js_skill ON job_skills(skill);"
            "CREATE INDEX idx_jc_job ON job_cities(job_id);"
            "CREATE INDEX idx_jc_city ON job_cities(city);"
        )


def main() -> None:
    tables = build_tables()
    write_outputs(tables)
    j = tables["jobs"]
    print(f"raw rows: {j.attrs['rows_raw']}  clean jobs: {len(j)}")
    print(f"skill links: {len(tables['job_skills'])}  city links: {len(tables['job_cities'])}")
    print(f"jobs with >=1 skill: {(j.n_skills > 0).mean():.1%}  with salary: {j.has_salary.mean():.1%}")
    print(j.role_family.value_counts().to_string())


if __name__ == "__main__":
    main()
