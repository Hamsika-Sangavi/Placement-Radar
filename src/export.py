"""Create the Excel workbook and the Power BI-ready CSV files.

Run:  python -m src.export
Writes exports/Placement_Radar.xlsx and exports/powerbi/*.csv
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from src import analysis as an
from src.skills import SKILL_CATEGORY

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports"

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="184F95")
INPUT_FILL = PatternFill("solid", fgColor="FFFF00")
BAND_FILL = PatternFill("solid", fgColor="F4F8FE")
THIN = Side(style="thin", color="D9D8D3")


def f(bold=False, color="000000", size=10, italic=False):
    return Font(name=FONT, bold=bold, color=color, size=size, italic=italic)


def style_header(ws, row: int, ncols: int) -> None:
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = f(True, "FFFFFF")
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def set_widths(ws, widths: dict[str, float]) -> None:
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def export_powerbi(jobs: pd.DataFrame, skills: pd.DataFrame, cities: pd.DataFrame) -> None:
    pbi = OUT / "powerbi"
    pbi.mkdir(parents=True, exist_ok=True)
    fact = jobs.drop(columns=["location_raw", "source_mode"]).copy()
    fact["posted_at"] = fact["posted_at"].dt.date
    for c in ["is_remote", "is_fresher_friendly", "has_salary", "in_hyderabad"]:
        fact[c] = fact[c].astype(int)
    fact.to_csv(pbi / "fact_jobs.csv", index=False)
    skills[["job_id", "skill"]].to_csv(pbi / "bridge_job_skills.csv", index=False)
    cities.to_csv(pbi / "bridge_job_cities.csv", index=False)
    dim = pd.DataFrame({"skill": list(SKILL_CATEGORY), "skill_category": list(SKILL_CATEGORY.values())})
    dim.to_csv(pbi / "dim_skill.csv", index=False)
    pd.DataFrame({"city": sorted(cities["city"].unique())}).to_csv(pbi / "dim_city.csv", index=False)


def build_workbook(jobs: pd.DataFrame, skills: pd.DataFrame) -> Path:
    wb = Workbook()
    roles = [r for r in sorted(jobs["role_family"].unique()) if r != "Other"] + ["Other"]

    # ------------------------------------------------------------ Read me
    ws = wb.active
    ws.title = "Read me"
    lines = [
        ("Placement Radar: Excel workbook", f(True, "184F95", 16)),
        ("Data and analytics hiring in India. Source: Naukri.com export (Kaggle, muhammetakkurt), snapshot Dec 2024.", f()),
        ("", f()),
        ("Sheets", f(True, size=11)),
        ("Jobs: one row per posting (cleaned). Skills are not stored here; see Job skills.", f()),
        ("Job skills: one row per posting-skill pair, with the role family added so Excel formulas can count by role.", f()),
        ("Skill demand: how many postings mention each skill (formulas).", f()),
        ("Role x skill: share of postings in each role that mention each top skill (formulas).", f()),
        ("Role summary: postings and fresher-friendly share per role (formulas).", f()),
        ("Gap checker: tick the skills you have, pick a role, see your coverage and what to learn next.", f()),
        ("", f()),
        ("How to use the Gap checker", f(True, size=11)),
        ("1. Open the Gap checker sheet. 2. Choose a role in the yellow cell B3. 3. Put 1 (have) or 0 (do not have) in the yellow column C.", f()),
        ("Coverage = demand-weighted share of the role's skills you already have. 'Learn next' lists the 5 skills with the highest demand that you lack.", f()),
        ("Blue text = input you can change. Black text = formula.", f()),
        ("", f()),
        ("Limits", f(True, size=11)),
        ("This is a one-time snapshot and cannot show trends. Only ~9% of postings show a salary, so no salary analysis is included.", f()),
        ("Skills are found by keyword matching in the title, tags and description. A mention is not the same as a requirement.", f()),
        ("The Python/Streamlit app also has a stricter 'ready for X% of postings' score. This workbook uses the simpler coverage score.", f()),
    ]
    for i, (text, font) in enumerate(lines, 1):
        ws.cell(row=i, column=1, value=text).font = font
    ws.column_dimensions["A"].width = 130
    ws.sheet_view.showGridLines = False

    # ------------------------------------------------------------ Jobs
    wj = wb.create_sheet("Jobs")
    jcols = ["job_id", "title", "role_family", "company", "exp_min", "exp_max", "exp_band",
             "is_fresher_friendly", "primary_city", "in_hyderabad", "company_rating", "n_skills"]
    heads = ["Job ID", "Title", "Role family", "Company", "Exp min (yrs)", "Exp max (yrs)", "Experience band",
             "Fresher-friendly (1/0)", "Primary city", "In Hyderabad (1/0)", "Company rating", "Skills found"]
    wj.append(heads)
    jj = jobs[jcols].copy()
    jj["is_fresher_friendly"] = jj["is_fresher_friendly"].astype(int)
    jj["in_hyderabad"] = jj["in_hyderabad"].astype(int)
    for row in jj.itertuples(index=False):
        wj.append([None if (isinstance(v, float) and pd.isna(v)) else v for v in row])
    n_jobs = len(jj)
    style_header(wj, 1, len(heads))
    wj.freeze_panes = "A2"
    wj.auto_filter.ref = f"A1:{get_column_letter(len(heads))}{n_jobs + 1}"
    set_widths(wj, {"A": 11, "B": 38, "C": 20, "D": 30, "E": 11, "F": 11, "G": 20, "H": 14, "I": 14, "J": 13, "K": 12, "L": 11})
    for r in wj.iter_rows(min_row=2, max_row=n_jobs + 1):
        for c in r:
            c.font = f()

    # ------------------------------------------------------------ Job skills
    wsk = wb.create_sheet("Job skills")
    wsk.append(["Job ID", "Skill", "Role family", "In Hyderabad (1/0)"])
    js = skills[["job_id", "skill"]].merge(jobs[["job_id", "role_family", "in_hyderabad"]], on="job_id")
    js["in_hyderabad"] = js["in_hyderabad"].astype(int)
    for row in js.itertuples(index=False):
        wsk.append(list(row))
    n_js = len(js)
    style_header(wsk, 1, 4)
    wsk.freeze_panes = "A2"
    set_widths(wsk, {"A": 11, "B": 24, "C": 20, "D": 18})
    JS_SKILL = f"'Job skills'!$B$2:$B${n_js + 1}"
    JS_ROLE = f"'Job skills'!$C$2:$C${n_js + 1}"
    JS_HYD = f"'Job skills'!$D$2:$D${n_js + 1}"
    J_ROLE = f"Jobs!$C$2:$C${n_jobs + 1}"
    J_FRESH = f"Jobs!$H$2:$H${n_jobs + 1}"
    J_HYD = f"Jobs!$J$2:$J${n_jobs + 1}"

    # ------------------------------------------------------------ Skill demand
    wd = wb.create_sheet("Skill demand")
    wd["A1"] = "Total postings"
    wd["A1"].font = f(True)
    wd["B1"] = f"=COUNTA(Jobs!$A$2:$A${n_jobs + 1})"
    wd["B1"].number_format = "#,##0"
    wd["B1"].font = f()
    wd.append([])
    wd.append(["Skill", "Category", "Postings", "% of postings", "Postings in Hyderabad", "% of Hyderabad postings"])
    style_header(wd, 3, 6)
    order = skills["skill"].value_counts().index.tolist()
    wd["H1"] = "Hyderabad postings"
    wd["H1"].font = f(True)
    wd["I1"] = f"=SUM({J_HYD})"
    wd["I1"].number_format = "#,##0"
    wd["I1"].font = f()
    for i, sk in enumerate(order, start=4):
        wd.cell(row=i, column=1, value=sk).font = f()
        wd.cell(row=i, column=2, value=SKILL_CATEGORY[sk]).font = f()
        wd.cell(row=i, column=3, value=f"=COUNTIF({JS_SKILL},A{i})").number_format = "#,##0"
        wd.cell(row=i, column=4, value=f"=C{i}/$B$1").number_format = "0.0%"
        wd.cell(row=i, column=5, value=f"=COUNTIFS({JS_SKILL},A{i},{JS_HYD},1)").number_format = "#,##0"
        wd.cell(row=i, column=5).font = f()
        wd.cell(row=i, column=6, value=f"=E{i}/$I$1").number_format = "0.0%"
        for c in (3, 4, 6):
            wd.cell(row=i, column=c).font = f()
    last = 3 + len(order)
    set_widths(wd, {"A": 26, "B": 18, "C": 12, "D": 14, "E": 22, "F": 24, "H": 20, "I": 12})
    wd.freeze_panes = "A4"
    ch = BarChart()
    ch.type = "bar"
    ch.title = "Top 15 skills (% of postings)"
    ch.style = 10
    ch.add_data(Reference(wd, min_col=4, min_row=3, max_row=18), titles_from_data=True)
    ch.set_categories(Reference(wd, min_col=1, min_row=4, max_row=18))
    ch.y_axis.number_format = "0%"
    ch.y_axis.majorGridlines = None
    ch.x_axis.scaling.orientation = "maxMin"
    ch.legend = None
    ch.roundedCorners = False
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    ch.series[0].graphicalProperties.solidFill = "2A78D6"
    ch.height, ch.width = 9, 16
    wd.add_chart(ch, "H4")

    # ------------------------------------------------------------ Role x skill
    wr = wb.create_sheet("Role x skill")
    top_skills = order[:14]
    wr["A1"] = "Share of postings in each role that mention the skill"
    wr["A1"].font = f(True, "184F95", 12)
    wr.append([])
    wr.cell(row=3, column=1, value="Role family")
    for j, sk in enumerate(top_skills, start=2):
        wr.cell(row=3, column=j, value=sk)
    wr.cell(row=3, column=len(top_skills) + 2, value="Postings in role")
    style_header(wr, 3, len(top_skills) + 2)
    for i, role in enumerate([r for r in roles if r != "Other"], start=4):
        wr.cell(row=i, column=1, value=role).font = f(True)
        for j in range(2, len(top_skills) + 2):
            col = get_column_letter(j)
            c = wr.cell(row=i, column=j, value=f"=COUNTIFS({JS_ROLE},$A{i},{JS_SKILL},{col}$3)/$P{i}")
            c.number_format = "0%"
            c.font = f()
            c.alignment = Alignment(horizontal="center")
        n = wr.cell(row=i, column=len(top_skills) + 2, value=f"=COUNTIF({J_ROLE},$A{i})")
        n.number_format = "#,##0"
        n.font = f()
    last_r = 3 + len([r for r in roles if r != "Other"])
    wr.conditional_formatting.add(
        f"B4:{get_column_letter(len(top_skills) + 1)}{last_r}",
        ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                       end_type="num", end_value=0.8, end_color="256ABF"),
    )
    set_widths(wr, {"A": 20, "P": 16})
    for j in range(2, len(top_skills) + 2):
        wr.column_dimensions[get_column_letter(j)].width = 12.5
    wr.row_dimensions[3].height = 32
    wr.freeze_panes = "B4"

    # ------------------------------------------------------------ Role summary
    wsu = wb.create_sheet("Role summary")
    wsu.append(["Role family", "Postings", "% of all postings", "Fresher-friendly postings", "Fresher-friendly %", "In Hyderabad"])
    style_header(wsu, 1, 6)
    for i, role in enumerate(roles, start=2):
        wsu.cell(row=i, column=1, value=role).font = f(True)
        wsu.cell(row=i, column=2, value=f"=COUNTIF({J_ROLE},A{i})").number_format = "#,##0"
        wsu.cell(row=i, column=3, value=f"=B{i}/'Skill demand'!$B$1").number_format = "0.0%"
        wsu.cell(row=i, column=4, value=f"=COUNTIFS({J_ROLE},A{i},{J_FRESH},1)").number_format = "#,##0"
        wsu.cell(row=i, column=5, value=f"=IF(B{i}=0,0,D{i}/B{i})").number_format = "0.0%"
        wsu.cell(row=i, column=6, value=f"=COUNTIFS({J_ROLE},A{i},{J_HYD},1)").number_format = "#,##0"
        for c in range(2, 7):
            wsu.cell(row=i, column=c).font = f()
    tr = len(roles) + 2
    wsu.cell(row=tr, column=1, value="Total").font = f(True)
    for col in "BDF":
        c = wsu[f"{col}{tr}"]
        c.value = f"=SUM({col}2:{col}{tr - 1})"
        c.number_format = "#,##0"
        c.font = f(True)
    wsu[f"E{tr}"] = f"=D{tr}/B{tr}"
    wsu[f"E{tr}"].number_format = "0.0%"
    wsu[f"E{tr}"].font = f(True)
    set_widths(wsu, {"A": 22, "B": 12, "C": 16, "D": 24, "E": 20, "F": 14})
    bc = BarChart()
    bc.type = "bar"
    bc.title = "Fresher-friendly share by role"
    bc.add_data(Reference(wsu, min_col=5, min_row=1, max_row=len(roles) + 1), titles_from_data=True)
    bc.set_categories(Reference(wsu, min_col=1, min_row=2, max_row=len(roles) + 1))
    bc.y_axis.number_format = "0%"
    bc.y_axis.majorGridlines = None
    bc.x_axis.scaling.orientation = "maxMin"
    bc.legend = None
    bc.roundedCorners = False
    bc.x_axis.delete = False
    bc.y_axis.delete = False
    bc.series[0].graphicalProperties.solidFill = "2A78D6"
    bc.height, bc.width = 8, 15
    wsu.add_chart(bc, "H2")

    # ------------------------------------------------------------ Gap checker
    wg = wb.create_sheet("Gap checker")
    wg["A1"] = "Skill gap checker"
    wg["A1"].font = f(True, "184F95", 14)
    wg["A3"] = "Target role"
    wg["A3"].font = f(True)
    wg["B3"] = "Data Analyst"
    wg["B3"].font = f(True, "0000FF")
    wg["B3"].fill = INPUT_FILL
    dv = DataValidation(type="list", formula1='"' + ",".join(r for r in roles if r != "Other") + '"', allow_blank=False)
    wg.add_data_validation(dv)
    dv.add("B3")
    wg["A4"] = "Postings in this role"
    wg["A4"].font = f(True)
    wg["B4"] = f"=COUNTIF({J_ROLE},B3)"
    wg["B4"].number_format = "#,##0"
    wg["A5"] = "Your coverage of demand"
    wg["A5"].font = f(True)
    first, lastg = 17, 17 + len(order) - 1
    wg["B5"] = f"=IF(SUM(D{first}:D{lastg})=0,0,SUMPRODUCT(C{first}:C{lastg},D{first}:D{lastg})/SUM(D{first}:D{lastg}))"
    wg["B5"].number_format = "0%"
    wg["B5"].font = f(True, size=12)
    wg["C5"] = "Share of the role's skill demand you already cover (each skill weighted by how often it is asked)"
    wg["C5"].font = f(italic=True, color="52514E")
    wg["B4"].font = f()

    wg["A7"] = "Learn next (highest demand among skills you lack)"
    wg["A7"].font = f(True, "184F95", 11)
    wg.append([])
    wg["A8"], wg["B8"], wg["C8"] = "Rank", "Skill", "Asked in % of postings"
    style_header(wg, 8, 3)
    for k in range(1, 6):
        r = 8 + k
        wg.cell(row=r, column=1, value=k).font = f()
        wg.cell(row=r, column=2, value=f'=IFERROR(INDEX($A${first}:$A${lastg},MATCH(A{r},$G${first}:$G${lastg},0)),"-")').font = f(True)
        c = wg.cell(row=r, column=3, value=f'=IFERROR(INDEX($D${first}:$D${lastg},MATCH(A{r},$G${first}:$G${lastg},0)),"")')
        c.number_format = "0%"
        c.font = f()
    wg["A15"] = "Tick your skills: 1 = I have it, 0 = I do not (yellow cells)"
    wg["A15"].font = f(True)
    for j, h in enumerate(["Skill", "Category", "I have it (1/0)", "Demand in role", "Priority score", "", "Rank among gaps"], start=1):
        wg.cell(row=16, column=j, value=h)
    style_header(wg, 16, 7)
    have_defaults = {"Python", "SQL", "Excel"}  # example row of realistic values; edit freely
    for i, sk in enumerate(order, start=first):
        wg.cell(row=i, column=1, value=sk).font = f()
        wg.cell(row=i, column=2, value=SKILL_CATEGORY[sk]).font = f()
        c = wg.cell(row=i, column=3, value=1 if sk in have_defaults else 0)
        c.font = f(True, "0000FF")
        c.fill = INPUT_FILL
        c.alignment = Alignment(horizontal="center")
        d = wg.cell(row=i, column=4, value=f"=IF($B$4=0,0,COUNTIFS({JS_ROLE},$B$3,{JS_SKILL},$A{i})/$B$4)")
        d.number_format = "0%"
        d.font = f()
        p = wg.cell(row=i, column=5, value=f"=D{i}*(1-C{i})+ROW()/1000000000")
        p.number_format = "0.000"
        p.font = f()
        rk = wg.cell(row=i, column=7, value=f'=IF(C{i}=1,"",RANK(E{i},$E${first}:$E${lastg}))')
        rk.font = f()
    dv01 = DataValidation(type="list", formula1='"0,1"', allow_blank=False)
    wg.add_data_validation(dv01)
    dv01.add(f"C{first}:C{lastg}")
    wg.conditional_formatting.add(f"D{first}:D{lastg}", ColorScaleRule(start_type="num", start_value=0, start_color="FFFFFF",
                                                                     end_type="num", end_value=0.8, end_color="86B6EF"))
    set_widths(wg, {"A": 30, "B": 22, "C": 24, "D": 16, "E": 14, "F": 3, "G": 16})

    path = OUT / "Placement_Radar.xlsx"
    OUT.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def main() -> None:
    jobs, skills, cities = an.load_tables()
    export_powerbi(jobs, skills, cities)
    p = build_workbook(jobs, skills)
    print("wrote", p)


if __name__ == "__main__":
    main()
