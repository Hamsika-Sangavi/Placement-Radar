# Build the Power BI report (about 45 minutes)

The `.pbix` file is not included because Power BI Desktop is a Windows app. These steps recreate the report from the CSV files in `exports/powerbi/`.
The DAX below was not run inside Power BI Desktop while writing this guide, so check each measure against the numbers in the Streamlit app (listed at the end).

## 1. Load the data
Home, Get data, Text/CSV. Load all five files:

| File | Rows | Role |
|---|---|---|
| `fact_jobs.csv` | one per posting | main table |
| `bridge_job_skills.csv` | one per posting-skill pair | many-to-many link |
| `bridge_job_cities.csv` | one per posting-city pair | many-to-many link |
| `dim_skill.csv` | one per skill | skill names and categories |
| `dim_city.csv` | one per city | city names |

In Power Query, set `job_id` to Whole number in all three job tables, and `posted_at` to Date.

## 2. Model (Model view)
Create these relationships. All are one-to-many with **single** filter direction (arrow from the "one" side to the "many" side):

- `fact_jobs[job_id]` (1) to `bridge_job_skills[job_id]` (many)
- `fact_jobs[job_id]` (1) to `bridge_job_cities[job_id]` (many)
- `dim_skill[skill]` (1) to `bridge_job_skills[skill]` (many)
- `dim_city[city]` (1) to `bridge_job_cities[city]` (many)

Single direction matters: a skill or city on a chart filters the bridge table, but does not shrink the posting total used as the denominator.

## 3. Measures
Create a table called `Measures` (Home, Enter data) and add:

```DAX
Total Postings = DISTINCTCOUNT ( fact_jobs[job_id] )

Fresher Share =
DIVIDE ( CALCULATE ( [Total Postings], fact_jobs[is_fresher_friendly] = 1 ), [Total Postings] )

Postings With Skill = DISTINCTCOUNT ( bridge_job_skills[job_id] )

Skill Share = DIVIDE ( [Postings With Skill], [Total Postings] )

Postings In City = DISTINCTCOUNT ( bridge_job_cities[job_id] )

Hyderabad Postings = CALCULATE ( [Total Postings], fact_jobs[in_hyderabad] = 1 )

Hyderabad Skill Share =
DIVIDE (
    CALCULATE ( [Postings With Skill], fact_jobs[in_hyderabad] = 1 ),
    [Hyderabad Postings]
)

Hyderabad Lift = DIVIDE ( [Hyderabad Skill Share], [Skill Share] )
```

## 4. Pages and visuals
Use one blue for normal bars (`#2A78D6`), orange (`#EB6834`) only for Hyderabad or the one item to look at, and a white-to-dark-blue scale for the heatmap.

1. **Overview**: cards for `Total Postings`, `Fresher Share`, `Hyderabad Postings`. Bar chart of `Total Postings` by `role_family`. Bar chart of top 12 `dim_skill[skill]` by `Skill Share` (use a Top N filter). Slicers for `role_family`, `exp_band`.
2. **Skills**: matrix with `role_family` on rows, `dim_skill[skill]` on columns, `Skill Share` as values, Top N 14 skills, and conditional formatting (background colour, white to blue).
3. **Cities and Hyderabad**: bar chart of `Postings In City` by `dim_city[city]` (Top N 10), with Hyderabad's bar set to orange. Bar chart of `Hyderabad Lift` by skill (filter skills with `Postings With Skill` over 300).
4. **Freshers**: bar chart of `Fresher Share` by `role_family`; column chart of `Total Postings` by `exp_band`.
5. **Skill gap (what-if)**: see below.

## 5. Skill gap page
Create a disconnected table of skills the user can pick:

```DAX
MySkill = SELECTCOLUMNS ( dim_skill, "skill", dim_skill[skill] )
```

Do not link it to anything. Add a multi-select slicer on `MySkill[skill]`, then add:

```DAX
Ready Postings =
COUNTROWS (
    FILTER (
        fact_jobs,
        VAR JobSkills = CALCULATETABLE ( VALUES ( bridge_job_skills[skill] ) )
        VAR N = COUNTROWS ( JobSkills )
        VAR Have = COUNTROWS ( INTERSECT ( JobSkills, VALUES ( MySkill[skill] ) ) )
        RETURN N >= 3 && DIVIDE ( Have, N ) >= 0.6
    )
)

Ready Share = DIVIDE ( [Ready Postings], [Total Postings] )
```

Show `Ready Share` as a card, with slicers for `role_family` and `is_fresher_friendly`. If the report is slow, add a filter so it only runs for one role.

## 6. Check your numbers
With no slicers selected, you should see (these match the Streamlit app and the SQL file):

- Total Postings: **13,679**
- Fresher Share: **14.4%**
- Hyderabad Postings: **2,458**
- Skill Share for SQL: **36.4%**; Python: **35.5%**
- Fresher Share for Business Analyst: **30.9%**; for Data Engineer: **7.1%**

If a number differs, check that all four relationships exist and use single filter direction.
