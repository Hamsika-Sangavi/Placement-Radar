"""Skill vocabulary and extraction.

The raw `tagsAndSkills` column from Naukri is noisy (it contains tokens such as
"Languages", "Data", "Processing"), so skills are extracted with a curated
vocabulary instead. Each skill has a category and a regex that is matched on the
job title, the tag list and the cleaned job description.
"""
from __future__ import annotations

import re

# (skill, category, regex). Regexes run on lowercase text.
SKILL_PATTERNS: list[tuple[str, str, str]] = [
    # Languages
    ("Python", "Language", r"\bpython\b"),
    ("SQL", "Language", r"\bsql\b|\bt-sql\b|\bpl/sql\b|\bpostgres(?:ql)?\b|\bmysql\b|\boracle sql\b"),
    ("R", "Language", r"\br programming\b|\br language\b|\brstudio\b|(?<=,)\s*r\s*(?=,|$)|^r\s*(?=,)"),
    ("Java", "Language", r"\bjava\b(?!\s*script)"),
    ("Scala", "Language", r"\bscala\b"),
    ("JavaScript", "Language", r"\bjavascript\b|\bnode\.?js\b|\breact(?:\.?js)?\b"),
    # BI and spreadsheets
    ("Excel", "BI & Reporting", r"\bexcel\b|\badvanced excel\b|\bvba\b"),
    ("Power BI", "BI & Reporting", r"\bpower\s?bi\b|\bpowerbi\b|\bdax\b"),
    ("Tableau", "BI & Reporting", r"\btableau\b"),
    ("Looker", "BI & Reporting", r"\blooker\b"),
    ("Qlik", "BI & Reporting", r"\bqlik(?:view|sense)?\b"),
    ("Google Analytics", "BI & Reporting", r"\bgoogle analytics\b|\bga4\b"),
    # Cloud
    ("AWS", "Cloud", r"\baws\b|\bamazon web services\b|\bredshift\b|\bglue\b|\bs3\b"),
    ("Azure", "Cloud", r"\bazure\b|\bsynapse\b|\badf\b|\bdata factory\b"),
    ("GCP", "Cloud", r"\bgcp\b|\bgoogle cloud\b|\bbigquery\b"),
    # Data engineering
    ("Spark", "Data Engineering", r"\bspark\b|\bpyspark\b"),
    ("Hadoop", "Data Engineering", r"\bhadoop\b|\bhdfs\b|\bhive\b|\bmapreduce\b"),
    ("Kafka", "Data Engineering", r"\bkafka\b"),
    ("Airflow", "Data Engineering", r"\bairflow\b"),
    ("Databricks", "Data Engineering", r"\bdatabricks\b"),
    ("Snowflake", "Data Engineering", r"\bsnowflake\b"),
    ("dbt", "Data Engineering", r"\bdbt\b"),
    ("ETL", "Data Engineering", r"\betl\b|\belt\b|\bssis\b|\binformatica\b|\bdata pipelines?\b"),
    ("Data Warehousing", "Data Engineering", r"\bdata warehous\w*|\bdwh\b"),
    ("Data Modeling", "Data Engineering", r"\bdata model\w*"),
    # Machine learning
    ("Machine Learning", "ML & AI", r"\bmachine learning\b|\bml\b"),
    ("Deep Learning", "ML & AI", r"\bdeep learning\b|\bneural networks?\b"),
    ("NLP", "ML & AI", r"\bnlp\b|\bnatural language processing\b"),
    ("Generative AI", "ML & AI", r"\bgenerative ai\b|\bgenai\b|\bllms?\b|\blarge language models?\b|\blangchain\b"),
    ("TensorFlow", "ML & AI", r"\btensorflow\b"),
    ("PyTorch", "ML & AI", r"\bpytorch\b"),
    ("Scikit-learn", "ML & AI", r"\bscikit[- ]learn\b|\bsklearn\b"),
    ("Computer Vision", "ML & AI", r"\bcomputer vision\b|\bopencv\b"),
    # Stats and analysis
    ("Statistics", "Analysis", r"\bstatistic\w*|\bhypothesis testing\b|\ba/b test\w*"),
    ("Pandas", "Analysis", r"\bpandas\b|\bnumpy\b"),
    ("Data Visualization", "Analysis", r"\bdata visuali[sz]ation\b|\bdashboards?\b"),
    ("SAS", "Analysis", r"\bsas\b"),
    # Databases
    ("NoSQL", "Database", r"\bnosql\b|\bmongodb\b|\bcassandra\b|\bdynamodb\b"),
    # Engineering tools
    ("Git", "Tools", r"\bgit\b|\bgithub\b|\bgitlab\b"),
    ("Docker", "Tools", r"\bdocker\b|\bkubernetes\b|\bk8s\b"),
    ("CI/CD", "Tools", r"\bci/cd\b|\bjenkins\b|\bdevops\b"),
    ("Jira", "Tools", r"\bjira\b|\bconfluence\b"),
    # Business and soft
    ("Stakeholder Management", "Business", r"\bstakeholders?\b"),
    ("Requirement Gathering", "Business", r"\brequirements? (?:gathering|analysis)\b|\bbrd\b|\buser stories\b"),
    ("Communication", "Business", r"\bcommunication\b|\bpresentation skills\b"),
]

SKILL_CATEGORY = {name: cat for name, cat, _ in SKILL_PATTERNS}
_COMPILED = [(name, re.compile(rx)) for name, _, rx in SKILL_PATTERNS]

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


def clean_text(html: str | None) -> str:
    """Strip HTML tags and collapse whitespace."""
    if not isinstance(html, str):
        return ""
    text = _TAG_RE.sub(" ", html.replace("<br>", " ").replace("<br/>", " "))
    return _SPACE_RE.sub(" ", text).strip()


def extract_skills(*texts: str | None) -> list[str]:
    """Return the sorted list of vocabulary skills found in the given texts."""
    blob = " , ".join(t.lower() for t in texts if isinstance(t, str) and t)
    if not blob:
        return []
    return sorted(name for name, rx in _COMPILED if rx.search(blob))
