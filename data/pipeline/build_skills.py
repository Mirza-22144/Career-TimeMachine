"""
Stage 1-2 of the CareerTimeMachine data pipeline.

Reads the raw O*NET Technology Skills export, filters it to IT occupations,
cleans the technology names, de-duplicates them, and writes a load-ready
skill catalogue.

Input :  software_skills.csv   (O*NET Technology Skills, 31,821 rows)
Output:  skills_clean.csv      (one row per unique technology)

Run:  python3 build_skills.py
"""

import csv
import re
from collections import defaultdict

RAW = "/mnt/user-data/uploads/software_skills.csv"
OUT = "/mnt/user-data/outputs/skills_clean.csv"
SOURCE_LABEL = "O*NET Technology Skills 30.2"

# ---------------------------------------------------------------
# 1. WHICH OCCUPATIONS TO KEEP
#    All IT-related occupations. Excludes pure-maths (actuaries,
#    statisticians), clinical/bio informatics, GIS, document mgmt,
#    and hardware engineering - none reflect a software engineer's stack.
# ---------------------------------------------------------------
IT_OCCUPATIONS = {
    # Core software
    "15-1252.00": "Software Developers",
    "15-1251.00": "Computer Programmers",
    "15-1253.00": "Software Quality Assurance Analysts and Testers",
    "15-1254.00": "Web Developers",
    "15-1255.00": "Web and Digital Interface Designers",
    "15-1255.01": "Video Game Designers",
    "15-1299.08": "Computer Systems Engineers/Architects",
    # Data
    "15-1242.00": "Database Administrators",
    "15-1243.00": "Database Architects",
    "15-1243.01": "Data Warehousing Specialists",
    "15-2051.00": "Data Scientists",
    "15-2051.01": "Business Intelligence Analysts",
    # Infrastructure / network
    "15-1241.00": "Computer Network Architects",
    "15-1244.00": "Network and Computer Systems Administrators",
    "15-1231.00": "Computer Network Support Specialists",
    "15-1232.00": "Computer User Support Specialists",
    "15-1241.01": "Telecommunications Engineering Specialists",
    # Security
    "15-1212.00": "Information Security Analysts",
    "15-1299.04": "Penetration Testers",
    "15-1299.05": "Information Security Engineers",
    "15-1299.06": "Digital Forensics Analysts",
    # Analysis / other tech
    "15-1211.00": "Computer Systems Analysts",
    "15-1221.00": "Computer and Information Research Scientists",
    "15-1299.01": "Web Administrators",
    "15-1299.07": "Blockchain Engineers",
    "15-1299.09": "Information Technology Project Managers",
    "11-3021.00": "Computer and Information Systems Managers",
}

# ---------------------------------------------------------------
# 2. NAME CLEANING
#    O*NET writes vendor-prefixed, spelled-out names. These rules
#    turn them into labels a returning engineer would recognise.
#    Explicit overrides first, then generic rules.
# ---------------------------------------------------------------
OVERRIDES = {
    "Amazon Web Services AWS software": "AWS",
    "Amazon Web Services AWS CloudFormation": "AWS CloudFormation",
    "Microsoft Azure software": "Microsoft Azure",
    "Cascading style sheets CSS": "CSS",
    "Hypertext markup language HTML": "HTML",
    "Extensible markup language XML": "XML",
    "JavaScript Object Notation JSON": "JSON",
    "Structured query language SQL": "SQL",
    "Oracle Java": "Java",
    "Oracle PL/SQL": "PL/SQL",
    "Google Angular": "Angular",
    "IBM Terraform": "Terraform",
    "The MathWorks MATLAB": "MATLAB",
    "Microsoft SQL Server Integration Services SSIS": "SSIS",
    "Relational database management system software": "Relational databases (RDBMS)",
    "JavaScript framework software": "JavaScript frameworks",
    "Web application software": "Web application frameworks",
    "Firewall software": "Firewalls",
    "Ansible software": "Ansible",
    "Informatica software": "Informatica",
    "Salesforce software": "Salesforce",
    "SAP software": "SAP",
    "Microsoft Office software": "Microsoft Office",
    "MITRE ATT&CK software": "MITRE ATT&CK",
    "Microsoft Playwright": "Playwright",
    "Microsoft PowerShell": "PowerShell",
    "Jenkins CI": "Jenkins",
    "Atlassian JIRA": "Jira",
    "Splunk Enterprise": "Splunk",
    "Tenable Nessus": "Nessus",
    "Apache Hadoop": "Hadoop",
    "Apache Spark": "Spark",
    "Apache Kafka": "Kafka",
    "Apache Airflow": "Airflow",
    "Apache JMeter": "JMeter",
    "Microsoft Active Directory": "Active Directory",
    "Microsoft Azure DevOps Services": "Azure DevOps",
    "Microsoft Azure Data Factory": "Azure Data Factory",
    "Amazon Elastic Compute Cloud EC2": "Amazon EC2",
    "Amazon Web Services AWS SageMaker": "AWS SageMaker",
    "Content management systems CMS": "Content management systems (CMS)",
    "Enterprise application integration EAI": "Enterprise integration (EAI)",
    "Content management systems CMS": "Content management (CMS)",
    "Microsoft Active Server Pages ASP": "ASP",
    "Microsoft Internet Information Services (IIS)": "IIS",
    "Microsoft Internet Information Services (IIS) Manager": "IIS Manager",
    "Microsoft SQL Server Reporting Services SSRS": "SSRS",
    "Microsoft Team Foundation Server": "Team Foundation Server",
    "Microsoft Visual Basic for Applications VBA": "VBA",
    "Oracle Java 2 Platform Enterprise Edition J2EE": "Java EE (J2EE)",
    "Oracle Primavera Enterprise Project Portfolio Management": "Oracle Primavera",
    "Unreal Technology Unreal Engine": "Unreal Engine",
    "Microsoft Visual Basic Scripting Edition VBScript": "VBScript",
}

# Trailing words that add nothing for a user-facing label
TRAILING_NOISE = re.compile(
    r"\s+(software|tool|tools|systems?|programs?|applications?)$", re.I
)


def clean_label(raw: str) -> str:
    """Turn an O*NET 'Workplace Example' into a readable technology name."""
    name = raw.strip()
    if name in OVERRIDES:
        return OVERRIDES[name]
    # drop a generic trailing noun ("Docker software" -> "Docker")
    name = TRAILING_NOISE.sub("", name).strip()
    # an override may only match after the trailing noun was stripped
    return OVERRIDES.get(name, name)


def make_id(label: str) -> str:
    """Stable lowercase snake_case id, safe for URLs and FKs."""
    slug = label.lower()
    slug = slug.replace("+", "plus").replace("#", "sharp").replace("&", "and")
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")[:64]


# ---------------------------------------------------------------
# 3. LOAD, FILTER, DEDUPE
# ---------------------------------------------------------------
def main():
    with open(RAW, newline="", encoding="utf-8-sig") as f:
        all_rows = list(csv.DictReader(f))

    it_rows = [r for r in all_rows if r["O*NET-SOC Code"] in IT_OCCUPATIONS]

    # Keep only technologies O*NET flags as currently relevant.
    # Showing all ~1,900 would be unusable in a checkbox list.
    flagged = [
        r for r in it_rows
        if r["Hot Technology"] == "Y" or r["In Demand"] == "Y"
    ]

    # Collapse duplicates: a technology appears once per occupation.
    # Keep the strongest signal seen for each flag, and record every
    # occupation and O*NET category it appeared under.
    merged = {}
    occ_seen = defaultdict(set)
    cat_seen = defaultdict(set)

    for r in flagged:
        label = clean_label(r["Workplace Example"])
        sid = make_id(label)
        if not sid:
            continue
        rec = merged.setdefault(sid, {
            "id": sid,
            "label": label,
            "category": r["Element Name"],
            "hot_technology": False,
            "in_demand": False,
            "source": SOURCE_LABEL,
        })
        rec["hot_technology"] |= (r["Hot Technology"] == "Y")
        rec["in_demand"] |= (r["In Demand"] == "Y")
        occ_seen[sid].add(IT_OCCUPATIONS[r["O*NET-SOC Code"]])
        cat_seen[sid].add(r["Element Name"])

    # ---------------------------------------------------------------
    # 4. WRITE OUTPUT
    # ---------------------------------------------------------------
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "id", "label", "category", "hot_technology", "in_demand",
            "source", "occurrences", "occupations",
        ])
        for sid in sorted(merged):
            rec = merged[sid]
            w.writerow([
                rec["id"], rec["label"], rec["category"],
                "true" if rec["hot_technology"] else "false",
                "true" if rec["in_demand"] else "false",
                rec["source"],
                len(occ_seen[sid]),
                "; ".join(sorted(occ_seen[sid])),
            ])

    # ---------------------------------------------------------------
    # 5. REPORT
    # ---------------------------------------------------------------
    print(f"raw rows            : {len(all_rows):,}")
    print(f"IT occupation rows  : {len(it_rows):,}  ({len(IT_OCCUPATIONS)} occupations)")
    print(f"hot / in-demand rows: {len(flagged):,}")
    print(f"unique skills out   : {len(merged):,}")
    print()
    both = sum(1 for r in merged.values() if r["hot_technology"] and r["in_demand"])
    print(f"  flagged in demand : {sum(1 for r in merged.values() if r['in_demand'])}")
    print(f"  flagged hot tech  : {sum(1 for r in merged.values() if r['hot_technology'])}")
    print(f"  flagged both      : {both}")
    print()
    print("Most widely used across occupations:")
    for sid in sorted(merged, key=lambda s: -len(occ_seen[s]))[:15]:
        print(f"  {len(occ_seen[sid]):2d}  {merged[sid]['label']}")
    print()
    print(f"written -> {OUT}")


if __name__ == "__main__":
    main()
