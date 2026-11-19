"""Placement Radar: dashboard for the Indian data and analytics job market (Naukri, Dec 2024 snapshot)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

from src import analysis as an
from src import charts as ch
from src.skills import SKILL_CATEGORY

st.set_page_config(page_title="Placement Radar", page_icon="📡", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;0,9..40,800;1,9..40,400&display=swap');

    *, html, body, [class*="css"], [data-testid="stAppViewContainer"],
    [data-testid="stHeader"], [data-testid="stSidebar"],
    .stMarkdown, .stRadio, button, input, select, textarea,
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"],
    [data-testid="stMetricDelta"], .stDataFrame, th, td,
    [data-testid="stWidgetLabel"], [data-testid="stMarkdownContainer"],
    .stSelectbox, .stMultiSelect, .stTextInput, p, span, label, div {
        font-family: 'DM Sans', sans-serif !important;
    }

    /* ---- kill top bar, push content flush ---- */
    [data-testid="stHeader"] {display: none !important;}
    .block-container {padding-top: 1.2rem !important; max-width: 1200px;}

    /* ---- main bg ---- */
    [data-testid="stAppViewContainer"] > section > div {
        background: #13111C;
    }

    /* ============ SIDEBAR ============ */
    section[data-testid="stSidebar"] {
        background: #0F0D18 !important;
        border-right: 1px solid rgba(124,92,252,0.06);
    }
    section[data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
        padding-top: 0.5rem !important;
    }
    section[data-testid="stSidebar"] > div:first-child > div:first-child {
        padding-top: 0 !important; margin-top: 0 !important;
    }
    /* Title */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        color: #ffffff !important; font-size: 1.65rem !important; font-weight: 700 !important;
        letter-spacing: -0.02em; margin: 0 !important; padding: 0 !important;
    }
    /* Caption */
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
        color: #9B97B0 !important; font-size: 0.82rem !important; margin: 0 !important;
    }
    /* Body text in sidebar */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #8B87A0 !important; font-size: 0.88rem; font-weight: 500;
    }
    /* Labels */
    [data-testid="stSidebar"] label {color: #8B87A0 !important; font-weight: 500; font-size: 0.85rem !important;}
    /* Nav items */
    [data-testid="stSidebar"] .stRadio label {
        padding: 0.4rem 0.7rem !important; border-radius: 10px; margin: 1px 0;
        transition: background 0.2s ease;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(124,92,252,0.08);
    }
    [data-testid="stSidebar"] .stRadio label span {
        color: #8B87A0 !important; font-size: 0.93rem; font-weight: 400;
        transition: color 0.2s ease;
    }
    [data-testid="stSidebar"] .stRadio label:hover span {
        color: #A78BFA !important;
    }
    [data-testid="stSidebar"] .stRadio label[data-checked="true"],
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[aria-checked="true"] {
        background: rgba(124,92,252,0.12) !important;
    }
    [data-testid="stSidebar"] .stRadio label[data-checked="true"] span,
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label[aria-checked="true"] span {
        color: #A78BFA !important; font-weight: 600;
    }
    [data-testid="stSidebar"] .stRadio > div {gap: 2px !important;}
    [data-testid="stSidebar"] hr {border-color: rgba(124,92,252,0.08) !important; margin: 0.6rem 0 !important;}

    /* ============ HEADINGS ============ */
    .block-container h1 {
        color: #ffffff !important; font-size: 1.85rem !important; font-weight: 700 !important;
        letter-spacing: -0.02em; line-height: 1.2; margin-bottom: 0.4rem;
    }
    h2 {color: #E8E6F0 !important; font-weight: 700; letter-spacing: -0.01em; font-size: 1.25rem !important;}
    h3 {color: #D4D1E0 !important; font-weight: 600;}

    /* ============ BODY TEXT ============ */
    .block-container p, .block-container li,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {
        color: #D4D1E0 !important; font-size: 0.95rem; line-height: 1.65;
    }
    .block-container strong, .block-container b {color: #ffffff !important;}
    .block-container em, .block-container i {color: #B8B4CC !important;}

    /* ============ METRIC CARDS ============ */
    [data-testid="stMetricValue"] {
        font-size: 2.1rem !important; color: #ffffff !important; font-weight: 700 !important;
        letter-spacing: -0.02em;
    }
    [data-testid="stMetricLabel"] p {
        color: #7B7893 !important; font-weight: 500 !important; font-size: 0.82rem !important;
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    [data-testid="stMetricDelta"] {color: #4ADE80 !important; font-weight: 600 !important;}
    [data-testid="stMetric"] {
        background: #1C1932;
        border-radius: 20px; padding: 1.2rem 1.4rem;
        border: 1px solid rgba(124,92,252,0.08);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(124,92,252,0.1), 0 4px 20px rgba(0,0,0,0.4);
        border-color: rgba(124,92,252,0.2);
    }

    /* ============ INSIGHT BOXES ============ */
    .insight {
        border-left: 3px solid #7C5CFC; padding: 0.75rem 1.2rem; margin: 0.6rem 0;
        background: rgba(124,92,252,0.06);
        border-radius: 0 14px 14px 0; color: #D4D1E0;
        font-size: 0.95rem; line-height: 1.6;
    }
    .insight b {color: #ffffff; font-weight: 600;}
    .note {color: #7B7893; font-size: 0.85rem;}

    /* ============ CHARTS ============ */
    .stPlotlyChart {
        border-radius: 20px;
        border: 1px solid rgba(124,92,252,0.06);
        background: #1C1932;
        padding: 0.6rem 0.2rem 0.2rem 0.2rem;
    }

    /* ============ DATA TABLES ============ */
    .stDataFrame {border-radius: 16px; overflow: hidden; border: 1px solid #252338;}
    [data-testid="stDataFrame"] [role="gridcell"] {font-size: 0.88rem;}

    /* ============ FORM ELEMENTS ============ */
    div[data-testid="stSelectbox"] label,
    div[data-testid="stMultiSelect"] label {
        color: #8B87A0 !important; font-weight: 500 !important; font-size: 0.88rem !important;
    }
    [data-testid="stCheckbox"] label span {color: #8B87A0 !important;}
    [data-testid="stMultiSelect"] [data-baseweb="tag"] {
        background: rgba(124,92,252,0.15) !important; border: 1px solid rgba(124,92,252,0.3) !important;
        border-radius: 8px !important; color: #D4D1E0 !important;
    }

    /* ============ BUTTONS ============ */
    div.stButton > button {
        background: linear-gradient(135deg, #7C5CFC 0%, #6344E0 100%);
        color: #ffffff; border: none; border-radius: 12px;
        font-weight: 600; font-size: 0.9rem;
        transition: all 0.25s ease; box-shadow: 0 2px 12px rgba(124,92,252,0.3);
    }
    div.stButton > button:hover {
        transform: translateY(-1px); box-shadow: 0 4px 20px rgba(124,92,252,0.45);
    }

    /* ============ CAPTIONS ============ */
    .stCaption p, [data-testid="stCaptionContainer"] p {
        color: #7B7893 !important; font-size: 0.85rem;
    }

    /* ============ ALERTS ============ */
    [data-testid="stAlert"] {
        border-radius: 14px; border: 1px solid #252338;
        background: #1C1932 !important;
    }

    /* ============ MISC ============ */
    hr {border-color: #252338 !important;}
    ::-webkit-scrollbar {width: 5px; height: 5px;}
    ::-webkit-scrollbar-track {background: #13111C;}
    ::-webkit-scrollbar-thumb {background: #252338; border-radius: 3px;}
    ::-webkit-scrollbar-thumb:hover {background: #2D2B3D;}

    /* ============ ANIMATIONS ============ */
    @keyframes fadeInUp {
        from {opacity: 0; transform: translateY(12px);}
        to {opacity: 1; transform: translateY(0);}
    }
    .block-container {animation: fadeInUp 0.4s ease-out;}
    .stPlotlyChart {animation: fadeInUp 0.5s ease-out 0.08s both;}
    [data-testid="stMetric"] {animation: fadeInUp 0.35s ease-out both;}
    [data-testid="stMetric"]:nth-child(2) {animation-delay: 0.04s;}
    [data-testid="stMetric"]:nth-child(3) {animation-delay: 0.08s;}
    [data-testid="stMetric"]:nth-child(4) {animation-delay: 0.12s;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load():
    return an.load_tables()


jobs, skills, cities = load()
ALL_ROLES = sorted(jobs["role_family"].unique())
CITY_ORDER = cities["city"].value_counts().head(12).index.tolist()
BANDS = ["Fresher (0-1 yrs)", "Junior (2-3 yrs)", "Mid (4-6 yrs)", "Senior (7+ yrs)"]

# ------------------------------------------------------------------ sidebar
st.sidebar.title("📡 Placement Radar")
st.sidebar.caption("Data & analytics hiring in India · Naukri snapshot, Dec 2024")
page = st.sidebar.radio(
    "Page",
    ["Overview", "Skills", "Cities and Hyderabad", "Freshers", "Companies", "Skill gap checker", "About the data"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.markdown("**Filters** (Overview, Skills, Companies)")
sel_roles = st.sidebar.multiselect("Role family", ALL_ROLES, default=[r for r in ALL_ROLES if r != "Other"])
sel_city = st.sidebar.selectbox("City", ["All cities"] + CITY_ORDER)
sel_bands = st.sidebar.multiselect("Experience", BANDS, default=BANDS)

view = an.filter_jobs(jobs, cities, sel_roles, sel_city, sel_bands)


def insight(text: str) -> None:
    st.markdown(f'<div class="insight">{text}</div>', unsafe_allow_html=True)


def need_data(df: pd.DataFrame) -> bool:
    if df.empty:
        st.warning("No jobs match these filters. Widen the role, city or experience selection.")
        return True
    return False


# ------------------------------------------------------------------ pages
if page == "Overview":
    st.title("What does the data and analytics job market look like?")
    if need_data(view):
        st.stop()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Job postings", f"{len(view):,}")
    c2.metric("Hiring companies", f"{view['company'].nunique():,}")
    c3.metric("Open to freshers (0-1 yrs)", f"{view['is_fresher_friendly'].mean():.0%}")
    c4.metric("Include Hyderabad", f"{view['job_id'].isin(cities.loc[cities.city == 'Hyderabad', 'job_id']).sum():,}")

    top = an.skill_demand(skills, view["job_id"], top=12)
    roles = view["role_family"].value_counts()
    if len(top) >= 3 and len(roles) >= 1:
        insight(f"<b>{top.iloc[0]['skill']}</b> and <b>{top.iloc[1]['skill']}</b> lead: they appear in "
                f"{top.iloc[0]['share']:.0%} and {top.iloc[1]['share']:.0%} of the selected postings.")
        fr = view.groupby("role_family")["is_fresher_friendly"].agg(["mean", "size"])
        fr = fr[fr["size"] >= 100].sort_values("mean", ascending=False)
        if len(fr) >= 2:
            insight(f"<b>{fr.index[0]}</b> is the most fresher-friendly role ({fr.iloc[0]['mean']:.0%} of postings accept 0-1 years). "
                    f"<b>{fr.index[-1]}</b> is the least ({fr.iloc[-1]['mean']:.0%}).")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(ch.hbar(roles.index, roles.values, "Postings by role family"), width="stretch")
    with right:
        st.plotly_chart(ch.hbar(top["skill"], top["share"] * 100, "Most requested skills", fmt="{:.0f}%",
                                hover=[f"{s}: {j:,} postings" for s, j in zip(top["skill"], top["jobs"])]),
                        width="stretch")

elif page == "Skills":
    st.title("Which skills does each role ask for?")
    if need_data(view):
        st.stop()
    st.caption("Share of postings that mention each skill. Skills are found in the title, tag list and description.")
    m = an.skill_by_role(view, skills, top_skills=14)
    if m.empty:
        st.info("Not enough data for the selected filters.")
    else:
        piv = m.pivot(index="role_family", columns="skill", values="share").fillna(0)
        order = piv.mean().sort_values(ascending=False).index
        st.plotly_chart(ch.heatmap(piv[order], "Skill demand by role (% of postings)", height=130 + 48 * len(piv)),
                        width="stretch")
    cat = st.selectbox("Skill category", ["All"] + sorted(set(SKILL_CATEGORY.values())))
    d = an.skill_demand(skills, view["job_id"])
    if cat != "All":
        d = d[d["skill_category"] == cat]
    d = d.head(15)
    st.plotly_chart(ch.hbar(d["skill"], d["share"] * 100, f"Top skills: {cat}", fmt="{:.0f}%",
                            hover=[f"{s}: {j:,} postings" for s, j in zip(d["skill"], d["jobs"])]),
                    width="stretch")

elif page == "Cities and Hyderabad":
    st.title("Where are the jobs, and what is different in Hyderabad?")
    cs = an.city_summary(jobs, cities, min_jobs=150).head(10)
    hyd_rank = list(an.city_summary(jobs, cities, min_jobs=1)["city"]).index("Hyderabad") + 1
    c1, c2, c3 = st.columns(3)
    hyd = cs[cs.city == "Hyderabad"].iloc[0]
    c1.metric("Hyderabad postings", f"{int(hyd['jobs']):,}")
    c2.metric("Rank among cities", f"#{hyd_rank}")
    c3.metric("Hyderabad: open to freshers", f"{hyd['fresher_share']:.0%}",
              delta=f"{(hyd['fresher_share'] - jobs['is_fresher_friendly'].mean()) * 100:+.1f} pts vs all India")
    st.caption("A posting that lists several cities counts once in each city, so city totals add up to more than the number of postings.")
    st.plotly_chart(ch.hbar(cs["city"], cs["jobs"], "Postings by city", highlight="Hyderabad"), width="stretch")

    hyd_ids = cities.loc[cities.city == "Hyderabad", "job_id"]
    all_sk = an.skill_demand(skills, jobs["job_id"]).set_index("skill")
    hy_sk = an.skill_demand(skills, hyd_ids).set_index("skill")
    comp = pd.DataFrame({"all": all_sk["share"] * 100, "hyd": hy_sk["share"] * 100, "jobs": all_sk["jobs"]}).dropna()
    comp = comp[comp["jobs"] >= 300].copy()
    comp["lift"] = comp["hyd"] / comp["all"]
    top_over = comp.sort_values("lift", ascending=False).head(8).reset_index().rename(columns={"index": "skill"})
    insight(f"Hyderabad postings ask for <b>{top_over.iloc[0]['skill']}</b> {top_over.iloc[0]['lift']:.1f}x as often as the rest of India. "
            f"Next: <b>{top_over.iloc[1]['skill']}</b> and <b>{top_over.iloc[2]['skill']}</b>.")
    st.plotly_chart(
        ch.dumbbell(top_over, "skill", "all", "hyd", "All India", "Hyderabad",
                    "Skills Hyderabad asks for more than India overall"),
        width="stretch",
    )

elif page == "Freshers":
    st.title("What can a fresher aim for?")
    st.caption("A posting is fresher-friendly when the minimum experience is 0 or 1 year.")
    rs = jobs.groupby("role_family").agg(jobs=("job_id", "size"), fresher=("is_fresher_friendly", "mean"))
    rs = rs[rs["jobs"] >= 150].sort_values("fresher", ascending=False)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(ch.hbar(rs.index, rs["fresher"] * 100, "Fresher-friendly share by role", fmt="{:.0f}%",
                                hover=[f"{r}: {f:.0%} of {n:,} postings" for r, f, n in zip(rs.index, rs["fresher"], rs["jobs"])]),
                        width="stretch")
    with c2:
        bands = jobs["exp_band"].value_counts().reindex(BANDS).dropna()
        st.plotly_chart(ch.vbar(bands.index, bands.values, "Postings by experience band", highlight="Fresher (0-1 yrs)"),
                        width="stretch")

    fr_ids = jobs.loc[jobs["is_fresher_friendly"], "job_id"]
    fr = an.skill_demand(skills, fr_ids).set_index("skill")
    al = an.skill_demand(skills, jobs["job_id"]).set_index("skill")
    comp = pd.DataFrame({"all": al["share"] * 100, "fresher": fr["share"] * 100}).dropna()
    comp = comp.sort_values("fresher", ascending=False).head(10).reset_index().rename(columns={"index": "skill"})
    insight(f"In fresher-friendly postings the top skills are <b>{comp.iloc[0]['skill']}</b> ({comp.iloc[0]['fresher']:.0f}%), "
            f"<b>{comp.iloc[1]['skill']}</b> ({comp.iloc[1]['fresher']:.0f}%) and <b>{comp.iloc[2]['skill']}</b> ({comp.iloc[2]['fresher']:.0f}%).")
    st.plotly_chart(ch.dumbbell(comp, "skill", "all", "fresher", "All postings", "Fresher-friendly postings",
                                "Skills that matter for 0-1 year roles"), width="stretch")
    st.markdown("**Companies that most often accept freshers**")
    cf = (jobs[jobs["is_fresher_friendly"]].groupby("company")
          .agg(fresher_jobs=("job_id", "size"), rating=("company_rating", "mean"))
          .query("fresher_jobs >= 5").sort_values("fresher_jobs", ascending=False).head(15).reset_index())
    cf["rating"] = cf["rating"].round(1)
    st.dataframe(cf, hide_index=True, width="stretch")

elif page == "Companies":
    st.title("Who is hiring, and how good are they to work for?")
    if need_data(view):
        st.stop()
    cs = an.company_summary(view, min_jobs=15)
    if cs.empty:
        st.info("No company has 15 or more postings under these filters.")
    else:
        top = cs.head(12)
        st.plotly_chart(ch.hbar(top["company"], top["jobs"], "Top hiring companies",
                                hover=[f"{c}: {j} postings · rating {r:.1f}" if pd.notna(r) else f"{c}: {j} postings"
                                       for c, j, r in zip(top["company"], top["jobs"], top["rating"])]),
                        width="stretch")
        rated = cs.dropna(subset=["rating"]).head(12)
        if len(rated) >= 3:
            st.plotly_chart(
                ch.hbar([f"{c} ({j})" for c, j in zip(rated["company"], rated["jobs"])], rated["rating"],
                        "Employee rating of the biggest hirers (postings in brackets)", fmt="{:.1f}",
                        hover=[f"{c}: rating {r:.1f} · {j} postings" for c, r, j in zip(rated["company"], rated["rating"], rated["jobs"])],
                        xtitle="AmbitionBox rating, out of 5"),
                width="stretch",
            )
        st.caption("Rating comes from AmbitionBox reviews included in the Naukri export. Companies without a rating are left out of the rating chart.")
        out = cs.copy()
        out["rating"] = out["rating"].round(1)
        out["fresher_share"] = (out["fresher_share"] * 100).round(0).astype(int).astype(str) + "%"
        st.dataframe(out.rename(columns={"jobs": "postings", "fresher_share": "fresher-friendly", "top_role": "most common role"}),
                     hide_index=True, width="stretch")

elif page == "Skill gap checker":
    st.title("How far am I from the market?")
    st.write("Pick the skills you have, the role you want and a city. You get the share of postings you are ready for "
             "and the next skills that unlock the most jobs.")
    vocab = sorted(SKILL_CATEGORY)
    c1, c2, c3 = st.columns([2, 1, 1])
    mine = c1.multiselect("My skills", vocab, default=["Python", "SQL", "Excel"])
    target = c2.multiselect("Target roles", [r for r in ALL_ROLES if r != "Other"], default=["Data Analyst", "Business Analyst"])
    city = c3.selectbox("City", ["All cities"] + CITY_ORDER, index=(CITY_ORDER.index("Hyderabad") + 1))
    fresher_only = st.checkbox("Only postings open to 0-1 years", value=True)

    pool = an.filter_jobs(jobs, cities, target or None, city, None)
    if fresher_only:
        pool = pool[pool["is_fresher_friendly"]]
    rep = an.gap_report(mine, pool, skills)
    if rep["n_jobs"] == 0:
        st.warning("Too few postings match this combination. Add roles, pick 'All cities' or untick the fresher filter.")
        st.stop()
    m1, m2, m3 = st.columns(3)
    m1.metric("Postings compared", f"{rep['n_jobs']:,}")
    m2.metric("You are ready for", f"{rep['ready_share']:.0%}", help="A posting counts when you already have 60% or more of its listed skills.")
    m3.metric("Average match", f"{rep['avg_match']:.0%}")
    if rep["n_jobs"] < 50:
        st.info("Small sample (under 50 postings). Treat the numbers as a rough guide.")
    sug = rep["suggestions"]
    if not sug.empty:
        insight(f"Learn <b>{sug.iloc[0]['skill']}</b> first: it makes you ready for <b>{int(sug.iloc[0]['unlocks'])}</b> more postings "
                f"({sug.iloc[0]['unlocks'] / rep['n_jobs']:.0%} of the sample).")
        st.plotly_chart(
            ch.hbar(sug["skill"], sug["unlocks"], "Extra postings you unlock by adding one skill",
                    highlight=sug.iloc[0]["skill"], integer_ticks=True,
                    hover=[f"{s}: +{u} postings · asked in {d:.0%} of the sample" for s, u, d in zip(sug["skill"], sug["unlocks"], sug["demand"])]),
            width="stretch",
        )
    st.markdown("**Best matching postings**")
    bm = an.best_matches(mine, pool, skills, top=15)
    bm["match"] = (bm["match"] * 100).round(0).astype(int)
    bm["experience"] = bm["exp_min"].astype(int).astype(str) + "-" + bm["exp_max"].astype(int).astype(str) + " yrs"
    st.dataframe(
        bm[["title", "company", "location_raw", "experience", "match", "missing_skills", "job_url"]].rename(
            columns={"location_raw": "location", "match": "match %", "missing_skills": "skills you lack", "job_url": "link"}),
        hide_index=True, width="stretch",
        column_config={"link": st.column_config.LinkColumn("link", display_text="open"),
                       "match %": st.column_config.ProgressColumn("match %", min_value=0, max_value=100, format="%d%%")},
    )

else:
    st.title("About the data")
    st.markdown(
        f"""
**Source.** A Naukri.com export of data and analytics job postings (Kaggle: *Naukri Jobs Dataset* by muhammetakkurt).
After removing duplicate job IDs: **{len(jobs):,} postings** from **{jobs['company'].nunique():,} companies**.

**Snapshot, not a trend.** Most postings were created in Nov-Dec 2024 (older ones were still live), so this shows hiring
at one point in time. It cannot show how demand changes month to month.

**What the numbers mean**
- *Skills* come from a curated list of {len(SKILL_CATEGORY)} skills matched in the title, tag list and description. The raw tag column is noisy, so it is not used alone.
- *Role family* is assigned from the job title with keyword rules. {int((jobs.role_family == 'Other').sum()):,} titles fall in "Other" and are hidden by default.
- *Fresher-friendly* = minimum experience of 0 or 1 year.
- *Cities*: a posting with several cities counts once in each. "Remote" postings are flagged but not counted as a city.
- *Match score* in the gap checker = share of a posting's listed skills that you have. "Ready" = 60% or more.

**Limits to keep in mind**
- Only **{jobs['has_salary'].mean():.0%}** of postings show a salary, so this project does not make salary claims.
- Skills mentioned in a description are not the same as skills required on the job.
- The data covers analytics, data and ML roles and some developer roles. It is not all of tech hiring.
        """
    )
