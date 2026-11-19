import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis import gap_report, skill_demand
from src.clean import experience_band, parse_experience, parse_locations, parse_salary_lpa, role_family
from src.skills import clean_text, extract_skills


def test_parse_experience():
    assert parse_experience("3-8 Yrs") == (3.0, 8.0)
    assert parse_experience("5 Yrs") == (5.0, 5.0)
    lo, hi = parse_experience(None)
    assert pd.isna(lo) and pd.isna(hi)


def test_parse_salary():
    assert parse_salary_lpa("10-20 Lacs PA") == (10.0, 20.0)
    assert parse_salary_lpa("20-10 Lacs PA") == (10.0, 20.0)  # reversed range is fixed
    assert pd.isna(parse_salary_lpa("Not disclosed")[0])
    assert pd.isna(parse_salary_lpa("20,000/month")[0])  # monthly figures are not guessed


def test_parse_locations_merges_aliases_and_flags_remote():
    cities, remote = parse_locations("Hyderabad/Secunderabad, Bangalore/Bengaluru(Dodda Nekkundi), Delhi / NCR")
    assert cities == ["Hyderabad", "Bengaluru", "Delhi"]
    assert remote is False
    cities, remote = parse_locations("Hybrid - Chennai, Pune")
    assert cities == ["Chennai", "Pune"]
    _, remote = parse_locations("Remote")
    assert remote is True


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Senior Data Engineer", "Data Engineer"),
        ("Machine Learning Engineer", "ML / AI Engineer"),
        ("Business Analyst", "Business Analyst"),
        ("Junior Data Analyst", "Data Analyst"),
        ("Power BI Developer", "BI / Reporting"),
        ("Data Scientist - NLP", "ML / AI Engineer"),
        ("Chief Happiness Officer", "Other"),
    ],
)
def test_role_family(title, expected):
    assert role_family(title) == expected


def test_experience_band():
    assert experience_band(0) == "Fresher (0-1 yrs)"
    assert experience_band(2) == "Junior (2-3 yrs)"
    assert experience_band(8) == "Senior (7+ yrs)"


def test_extract_skills_uses_word_boundaries():
    found = extract_skills("Data Analyst", "SQL,Power BI", "<p>We use <b>Python</b> and MySQL. Javascript too.</p>")
    assert {"SQL", "Power BI", "Python", "JavaScript"} <= set(found)
    assert "Java" not in found  # 'javascript' must not count as Java
    assert "R" not in extract_skills("Researcher at BrightRoad", None, "r&d work")


def test_clean_text_strips_html():
    assert clean_text("<p>Hello<br>world</p>") == "Hello world"


def _toy():
    jobs = pd.DataFrame({"job_id": [1, 2, 3, 4], "role_family": ["Data Analyst"] * 4})
    rows = []
    for jid, sks in {
        1: ["SQL", "Excel", "Power BI"],
        2: ["SQL", "Excel", "Python"],
        3: ["SQL", "Tableau", "Statistics"],
        4: ["Spark", "AWS", "Python"],
    }.items():
        rows += [(jid, s) for s in sks]
    return jobs, pd.DataFrame(rows, columns=["job_id", "skill"]).assign(skill_category="x")


def test_skill_demand_share():
    jobs, skills = _toy()
    d = skill_demand(skills, jobs["job_id"]).set_index("skill")
    assert d.loc["SQL", "share"] == 0.75


def test_gap_report_counts_ready_jobs_and_suggests_best_skill():
    jobs, skills = _toy()
    rep = gap_report(["SQL", "Excel"], jobs, skills, ready_threshold=0.6)
    # job1: 2/3 ready, job2: 2/3 ready, job3: 1/3 not ready, job4: 0 not ready
    assert rep["n_jobs"] == 4 and rep["ready"] == 2
    sug = rep["suggestions"].set_index("skill")
    # adding Tableau makes job3 ready (2/3); adding Python makes nothing new ready for job4 (1/3)
    assert sug.loc["Tableau", "unlocks"] == 1
    assert sug.loc["Python", "unlocks"] == 0
