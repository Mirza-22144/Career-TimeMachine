"""
  Fig 1  Skills per role                      (Hindsight)
  Fig 2  Flag distribution                     (Insight)
  Fig 3  Top 20 technologies by breadth         (Hindsight)
  Fig 4  Bright Outlook by occupation     - which roles are growing  (Foresight)
  Fig 5  JSA projected growth to 2035     - Australian demand        (Foresight)
  Fig 6  IVI job-ad volume over time      - what changed since 2021  

INPUTS   
  DS-01  data/processed/skills_clean.csv                  from build_skills.py
  DS-01  data/raw/software_skills.csv                     O*NET Technology Skills
  DS-02  data/raw/All_Bright_Outlook_Occupations.csv      O*NET Bright Outlook
  DS-03  data/raw/employment_projections_2025_2035.xlsx   JSA
  DS-04  data/raw/internet_vacancies_anzsco4.xlsx         JSA IVI

"""

import csv
import os
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")          
import matplotlib.pyplot as plt
import pandas as pd


SKILLS_CLEAN = "data/processed/skills_clean.csv"
ONET_RAW     = "data/raw/software_skills.csv"
BRIGHT       = "data/raw/All_Bright_Outlook_Occupations.csv"
PROJECTIONS  = "data/raw/employment_projections_2025_2035.xlsx"
IVI          = "data/raw/internet_vacancies_anzsco4.xlsx"
FIGDIR       = "docs/figures"

# we take one consistent palette 
PURPLE, NAVY, GREY, AMBER, GREEN = "#5B2C8D", "#1F3864", "#9E9E9E", "#B45309", "#0F6E56"

plt.rcParams.update({
    "font.family": "serif",      
    "font.size": 9,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.spines.top": False,     # remove the top and right box lines less clutter
    "axes.spines.right": False,
    "figure.dpi": 300,
})


def save(fig, name):
    """Write a figure to docs/figures and close it to free memory."""
    os.makedirs(FIGDIR, exist_ok=True)
    path = f"{FIGDIR}/{name}.png"
    fig.savefig(path, bbox_inches="tight")   # bbox inches trims whitespace
    plt.close(fig)
    print(f"  saved -> {path}")


# all the 27 IT occupations 
IT_OCCUPATIONS = {
    "15-1252.00": "Software Developers",
    "15-1251.00": "Computer Programmers",
    "15-1253.00": "Software QA Analysts and Testers",
    "15-1254.00": "Web Developers",
    "15-1255.00": "Web and Digital Interface Designers",
    "15-1255.01": "Video Game Designers",
    "15-1299.08": "Computer Systems Engineers/Architects",
    "15-1242.00": "Database Administrators",
    "15-1243.00": "Database Architects",
    "15-1243.01": "Data Warehousing Specialists",
    "15-2051.00": "Data Scientists",
    "15-2051.01": "Business Intelligence Analysts",
    "15-1241.00": "Computer Network Architects",
    "15-1244.00": "Network and Systems Administrators",
    "15-1231.00": "Computer Network Support Specialists",
    "15-1232.00": "Computer User Support Specialists",
    "15-1241.01": "Telecommunications Engineering Specialists",
    "15-1212.00": "Information Security Analysts",
    "15-1299.04": "Penetration Testers",
    "15-1299.05": "Information Security Engineers",
    "15-1299.06": "Digital Forensics Analysts",
    "15-1211.00": "Computer Systems Analysts",
    "15-1221.00": "Computer and Information Research Scientists",
    "15-1299.01": "Web Administrators",
    "15-1299.07": "Blockchain Engineers",
    "15-1299.09": "IT Project Managers",
    "11-3021.00": "Computer and Information Systems Managers",
}


# function for skills per role 
# technologies per role
def figure_1_skills_per_role():
    print("\nFigure 1 - skills per role")

    # Read the raw ONET file and count DISTINCT technologies per occupation.
    # A set is used rather than a list because the same technology can be used for more occupations 
    per_role = defaultdict(set)
    with open(ONET_RAW, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            code = r["O*NET-SOC Code"]
            if code in IT_OCCUPATIONS:
                per_role[IT_OCCUPATIONS[code]].add(r["Workplace Example"])

    counts = {role: len(techs) for role, techs in per_role.items()} # asc to desc
    counts = dict(sorted(counts.items(), key=lambda kv: kv[1]))   
                                                                  
    print(f"  roles: {len(counts)}")
    print(f"  max  : {max(counts.values())} ({max(counts, key=counts.get)})")
    print(f"  min  : {min(counts.values())} ({min(counts, key=counts.get)})")
    print(f"  mean : {sum(counts.values()) / len(counts):.0f}")

    fig, ax = plt.subplots(figsize=(7.2, 7))
    # we highlight the software developers in purple as that was our persona role 

    colours = [PURPLE if r == "Software Developers" else NAVY for r in counts]
    ax.barh(list(counts), list(counts.values()), color=colours, height=0.72)
    ax.set_xlabel("Distinct technologies in the catalogue")
    ax.set_title("Figure 1  Catalogue coverage by IT role\nO*NET Technology Skills v30.2, 27 IT occupations")


    for i, v in enumerate(counts.values()):
        ax.text(v + 4, i, str(v), va="center", fontsize=7.5)
    ax.margins(x=0.10)
    save(fig, "fig1_skills_per_role")


# figure 2 shows the flags in demand or hot tech
# also justify why we keep unflagged tech as it would remove 84 % data 
def figure_2_flag_distribution():
    print("\nFigure 2 - flag distribution")

    df = pd.read_csv(SKILLS_CLEAN)
    # csv stores booleans as the strings "true"/"false" because that is what postgres expects 
    df["in_demand"] = df["in_demand"].astype(str).str.lower() == "true"
    df["hot_technology"] = df["hot_technology"].astype(str).str.lower() == "true"

    both = int((df.in_demand & df.hot_technology).sum())
    demand_only = int((df.in_demand & ~df.hot_technology).sum())
    hot_only = int((~df.in_demand & df.hot_technology).sum())
    neither = int((~df.in_demand & ~df.hot_technology).sum())

    print(f"  total          : {len(df)}")
    print(f"  both flags     : {both}")
    print(f"  in demand only : {demand_only}")
    print(f"  hot only       : {hot_only}")
    print(f"  neither        : {neither}  ({neither/len(df)*100:.1f}%)")

    labels = ["Both flags", "In Demand only", "Hot Technology only", "No flag"]
    values = [both, demand_only, hot_only, neither]
    colours = [PURPLE, NAVY, AMBER, GREY]

    fig, ax = plt.subplots(figsize=(7, 3.4))
    bars = ax.bar(labels, values, color=colours, width=0.6)
    ax.set_ylabel("Technologies")
    ax.set_title("Figure 2  Currency flags across the skill catalogue\n1,299 technologies, O*NET v30.2")
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width()/2, v + 15, str(v), ha="center", fontsize=8.5)
    ax.margins(y=0.18)
    save(fig, "fig2_flag_distribution")


# below function is for top 20 technologies 
# also shows which tech appears across all roles 
def figure_3_breadth():
    print("\nFigure 3 - technologies by occupation breadth")

    df = pd.read_csv(SKILLS_CLEAN)
    # occurrences was written by build_skills.py: the number of distinct
    top = df.nlargest(20, "occurrences")[["label", "occurrences"]]
    top = top.sort_values("occurrences")          # ascending for a horizontal bar

    print(f"  highest: {top.occurrences.max()} of 27 occupations")
    print(f"  at max : {', '.join(top[top.occurrences == top.occurrences.max()].label)}")

    fig, ax = plt.subplots(figsize=(7.2, 5.6))
    ax.barh(top.label, top.occurrences, color=NAVY, height=0.72)
    ax.set_xlabel("Number of IT occupations using this technology (max 27)")
    ax.set_title("Figure 3  Most widely used technologies across IT roles\nO*NET Technology Skills v30.2")
    ax.axvline(27, color=GREY, linestyle=":", linewidth=1)   # reference line at the max
    ax.text(27, -0.9, "all 27", fontsize=7, color=GREY, ha="center")
    for i, v in enumerate(top.occurrences):
        ax.text(v + 0.2, i, str(v), va="center", fontsize=7.5)
    ax.margins(x=0.08)
    save(fig, "fig3_breadth")


# we use the bright outlook dataset here
# which jobs are expected to grow 
def figure_4_bright_outlook():
    print("\nFigure 4 - Bright Outlook status")

    # Join Bright Outlook onto our 27 occupations, keyed on O*NET-SOC code
    # using O*NET SOC code 
    with open(BRIGHT, newline="", encoding="utf-8-sig") as f:
        bo = {r["Code"]: r["Categories"] for r in csv.DictReader(f)}

    buckets = Counter()
    for code, name in IT_OCCUPATIONS.items():
        cats = bo.get(code)
        if cats is None:
            buckets["Not flagged"] += 1
        elif "New and Emerging" in cats:
            buckets["New and Emerging"] += 1
        elif "Numerous Job Openings" in cats and "Rapid Growth" in cats:
            buckets["Rapid Growth +\nNumerous Openings"] += 1
        elif "Rapid Growth" in cats:
            buckets["Rapid Growth"] += 1
        else:
            buckets["Numerous Openings"] += 1

    for k, v in buckets.items():
        print(f"  {k.replace(chr(10),' '):32} {v}")

    order = ["New and Emerging", "Rapid Growth +\nNumerous Openings",
             "Rapid Growth", "Numerous Openings", "Not flagged"]
    order = [o for o in order if o in buckets]
    values = [buckets[o] for o in order]
    colours = [GREEN, PURPLE, NAVY, AMBER, GREY][:len(order)]

    fig, ax = plt.subplots(figsize=(7, 3.6))
    bars = ax.bar(order, values, color=colours, width=0.6)
    ax.set_ylabel("IT occupations")
    ax.set_title("Figure 4  Growth outlook across the 27 IT occupations\nO*NET Bright Outlook, 2024\u20132034 projections")
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width()/2, v + 0.2, str(v), ha="center", fontsize=8.5)
    ax.margins(y=0.20)
    save(fig, "fig4_bright_outlook")


# function which visualises according to australian evidence if the occupations are growing in australai or not
def figure_5_jsa_projections():
    print("\nFigure 5 - JSA employment projections")

    # Table_6 holds ANZSCO 4-digit unit groups
    # skiprows=8 lands on the first data row.
    df = pd.read_excel(PROJECTIONS, sheet_name="Table_6 Occupation Unit Group",
                       skiprows=8)
    df.columns = [str(c).strip() for c in df.columns]

    code_col = df.columns[2]
    name_col = df.columns[3]
    base_col = df.columns[5]     # employment at May 2025
    proj_col = df.columns[7]     # projected employment at May 2035

    # code column is read as float, 2613.0 if casted to int would fail to show a match
    df["anzsco"] = pd.to_numeric(df[code_col], errors="coerce")
    ict = df[df.anzsco.isin([2611, 2612, 2613, 2621, 2631, 2632, 2633, 1351])].copy()
    ict["anzsco"] = ict.anzsco.astype(int).astype(str)
    code_col = "anzsco"

    ict["growth_pct"] = (ict[proj_col] - ict[base_col]) / ict[base_col] * 100
    ict = ict.dropna(subset=["growth_pct"]).sort_values("growth_pct")

    for _, r in ict.iterrows():
        print(f"  {r[code_col]}  {str(r[name_col])[:48]:48} {r['growth_pct']:+.1f}%")

    fig, ax = plt.subplots(figsize=(7.2, 4))
    labels = [str(n)[:46] for n in ict[name_col]]
    # Highlight Software and Applications Programmers 
    colours = [PURPLE if "Software" in str(n) else NAVY for n in ict[name_col]]
    ax.barh(labels, ict.growth_pct, color=colours, height=0.68)
    ax.set_xlabel("Projected employment growth, May 2025 to May 2035 (%)")
    ax.set_title("Figure 5  Australian ICT employment projections\nJobs and Skills Australia, 2025\u20132035")
    for i, v in enumerate(ict.growth_pct):
        ax.text(v + 0.3, i, f"{v:+.1f}%", va="center", fontsize=7.5)
    ax.margins(x=0.14)
    save(fig, "fig5_jsa_projections")


# IVI job as volume over time 
def figure_6_ivi_timeseries():
    print("\nFigure 6 - IVI job advertisement volume")

    df = pd.read_excel(IVI, sheet_name="4 digit 3 month average")

    # all it occupation ar eplotted using time series data 
    tracked = {
        "2613": "Software and Applications Programmers",
        "2611": "ICT Business and Systems Analysts",
        "2612": "Multimedia Specialists and Web Developers",
        "2621": "Database and Systems Admin, ICT Security",
        "2631": "Computer Network Professionals",
        "2632": "ICT Support and Test Engineers",
        "2633": "Telecommunications Engineering Professionals",
        "1351": "ICT Managers",
    }
    df["ANZSCO_CODE"] = df["ANZSCO_CODE"].astype(str)
    sub = df[(df.ANZSCO_CODE.isin(tracked)) & (df.state == "AUST")]

    # Columns 3 onward are the monthly date columns.
    date_cols = list(df.columns[3:])

    # software developer line is thickend 
    others = plt.cm.Blues([0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95])

    fig, ax = plt.subplots(figsize=(8, 4.6))
    peak_info = {}
    other_i = 0

    for code, label in tracked.items():
        row = sub[sub.ANZSCO_CODE == code]
        if row.empty:
            print(f"  WARNING: {code} not found in the IVI file")
            continue

        # Reshape wide to long: one row per month for this occupation.
        series = pd.to_numeric(row[date_cols].iloc[0], errors="coerce")
        series.index = pd.to_datetime(date_cols)
        series = series[series.index >= "2015-01-01"]     # last decade only

        if code == "2613":
            ax.plot(series.index, series.values, label=label,
                    color=PURPLE, linewidth=2.0, zorder=5)
        else:
            ax.plot(series.index, series.values, label=label,
                    color=others[other_i], linewidth=1.1)
            other_i += 1

        # Record peak and latest for every group

        peak_val = series.max()
        peak_date = series.idxmax()
        latest = series.iloc[-1]
        change = (latest - peak_val) / peak_val * 100
        peak_info[code] = (label, peak_date, peak_val, latest, change)

    print(f"  {'ANZSCO':7} {'peak':>10}  {'latest':>8}  {'change':>8}")
    for code, (label, pd_, pv, lv, ch) in peak_info.items():
        print(f"  {code:7} {pv:10,.0f}  {lv:8,.0f}  {ch:+7.1f}%   {label[:40]} (peak {pd_.date()})")

    # 
    ax.axvspan(pd.Timestamp("2021-01-01"), pd.Timestamp("2023-01-01"),
               color=GREY, alpha=0.16, zorder=0)
    # Placed low so it does not collide with the legend at the top left.
    ax.text(pd.Timestamp("2022-01-01"), ax.get_ylim()[1] * 0.06,
            "illustrative\ncareer break", ha="center", fontsize=7.5, color="#444444")

    ax.set_ylabel("Online job advertisements (3-month average)")
    ax.set_title("Figure 6  Australian ICT job advertisement volume\n"
                 "JSA Internet Vacancy Index, national, all eight ANZSCO ICT groups, 2015\u20132026")
    ax.legend(frameon=False, fontsize=7, loc="upper left", ncol=2)
    ax.margins(y=0.12)
    save(fig, "fig6_ivi_timeseries")

if __name__ == "__main__":
    print("=" * 72)
    print("CareerTimeMachine - preliminary analysis")
    print("=" * 72)
    figure_1_skills_per_role()
    figure_2_flag_distribution()
    figure_3_breadth()
    figure_4_bright_outlook()
    figure_5_jsa_projections()
    figure_6_ivi_timeseries()
    print("\nAll figures written to", FIGDIR)
