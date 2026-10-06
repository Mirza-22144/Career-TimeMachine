"""
build_vacancy_seed.py

Reads the JSA Internet Vacancy ad job index and we write 3 sql seed files

    seed_anzsco_occupation.sql   the ANZSCO groups we use
    seed_role_anzsco_map.sql     our role -> ANZSCO crosswalk
    seed_vacancy_monthly.sql     monthly ad counts for those groups
"""

# lets us build the file paths and the folders 
import os        
                            
import sys           
# reads excel file into a table                        
import pandas as pd                       

# we use the default repo path 
IVI_XLSX = (sys.argv[1] if len(sys.argv) > 1 else
            "data/raw/internet_vacancies_anzsco4_occupations_states_and_"
            "territories_-_august_2026.xlsx")             # the IVI download
OUT_DIR = sys.argv[2] if len(sys.argv) > 2 else "data/seed"  # where seed files go
# sheet taht holds the job ad data 
SHEET = "4 digit 3 month average"        
# provenance text written in each file as per the cc by 4.0 guidelines                   
SOURCE = "JSA Internet Vacancy Index, August 2026 (CC BY 4.0)"


# handwritten link for each role from US BASED O*NET to Australian ANZSCO 
# ANZSCO in 4 digit code for every job 
# we use a confidence metric 
#   confidence high = Australia has the same named job; medium = same work, mixed group;
#    low = no Australian equivalent
ROLE_TO_ANZSCO = { # start of the dict 
    "software_developer": ("2613", "high",
        "Software Engineer and Developer Programmer both sit in 2613."),
    "computer_programmer": ("2613", "high",
        "Analyst Programmer and Developer Programmer sit in 2613."),
    "blockchain_engineer": ("2613", "low", # no blockchain code so using the confidence interval it is advertised as software engineers
        "ANZSCO has no blockchain code; these roles are advertised as software engineers."),
    "software_qa_analyst_tester": ("2632", "medium",
        "ICT Quality Assurance and Systems Test Engineers are in 2632, but the group also includes support engineers."),
    "web_developer": ("2612", "high",
        "Web Developer is a named occupation in 2612."),
        # multimedia specialists and web developers
    "web_and_digital_interface_designer": ("2324", "medium",
        "Web Designer sits in 2324; the group also includes graphic designers and illustrators."),
    "video_game_designer": ("2612", "low",
        "No ANZSCO game designer code; Multimedia Specialist in 2612 is the closest."),
    "web_administrator": ("3131", "high",
        "Web Administrator is a named occupation in 3131 ICT Support Technicians."),
    "computer_systems_analyst": ("2611", "high",
        "Systems Analyst is a named occupation in 2611."), # ICT business and systems 
    "business_intelligence_analyst": ("2611", "medium",
        "BI roles are usually advertised as ICT Business Analyst, which sits in 2611."),
    "data_scientist": ("2611", "low",
        "ANZSCO 1.3 has no data scientist code; ads split between 2611 and statisticians."),
    "computer_and_information_research_scientist": ("2611", "low",
        "No ANZSCO computing research code; 2611 is the nearest group."),
    "database_administrator": ("2621", "high",
        "Database Administrator is a named occupation in 2621."), # database and system administrator 
    "database_architect": ("2621", "high",
        "Database work sits in 2621; ANZSCO has no separate database architect."),
    "data_warehousing_specialist": ("2621", "medium",
        "Warehousing is database work, so 2621, but no named occupation matches."),
    "network_and_systems_administrator": ("2621", "high",
        "Systems Administrator is a named occupation in 2621."),
    "information_security_analyst": ("2621", "medium",
        "ICT Security Specialist is in 2621, shared with database and systems administrators."), # database and system admin, ICT Security
    "information_security_engineer": ("2621", "low",
        "Counted under ICT Security Specialist; no separate engineer code."),
    "penetration_tester": ("2621", "low",
        "Counted under ICT Security Specialist; no separate code."),
    "digital_forensics_analyst": ("2621", "low",
        "Counted under ICT Security Specialist; no separate code."),
    "computer_network_architect": ("2631", "high",
        "Network engineers and analysts sit in 2631 Computer Network Professionals."),
    "computer_systems_engineer_architect": ("2631", "medium",
        "Systems engineering sits in 2631; solution architects also appear in 2611."),
    "computer_network_support_specialist": ("3131", "medium",
        "Network support technicians are in 3131; more senior support may sit in 2632."),
    "computer_user_support_specialist": ("3131", "high",
        "ICT Customer Support Officer (help desk) is a named occupation in 3131."),
    "telecommunications_engineering_specialist": ("2633", "high",
        "Telecommunications engineers are a named group, 2633."),
    "it_project_manager": ("1351", "medium",
        "ICT Project Manager is in 1351, but the group also includes CIOs and ICT managers."),
    "computer_and_information_systems_manager": ("1351", "high",
        "Chief Information Officer and ICT Manager both sit in 1351."),
}

# national total , all the 8 states and territories 
# we only consider aus
STATES = ["AUST", "NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]


def q(text):
    # wraps the text in single quotes for sql
    return "'" + str(text).replace("'", "''") + "'"


# load the data sheet into dataframe 
ivi = pd.read_excel(IVI_XLSX, sheet_name=SHEET)            # whole sheet into a table
# make the code plain text with no spaces 
ivi["ANZSCO_CODE"] = ivi["ANZSCO_CODE"].astype(str).str.strip()  

codes_needed = sorted({v[0] for v in ROLE_TO_ANZSCO.values()})  # only groups we actually map to
# keeps only the rows for those 10 groups 
ivi = ivi[ivi["ANZSCO_CODE"].isin(codes_needed) & ivi["state"].isin(STATES)]

missing = set(codes_needed) - set(ivi["ANZSCO_CODE"])     # fail loudly if a code is not in the file
assert not missing, f"ANZSCO codes not found in IVI file: {missing}"

month_cols = [c for c in ivi.columns if not isinstance(c, str)]  # date columns are the months

# quality checks 

# turn every month cell into a number 
values = ivi[month_cols].apply(pd.to_numeric, errors="coerce")  # '.' becomes NaN
suppressed = int(values.isna().sum().sum())                # how many cells JSA left blank
print(f"suppressed cells  : {suppressed} in our groups")


# national figures 
nat = values[ivi["state"] == "AUST"].set_index(ivi.loc[ivi["state"] == "AUST", "ANZSCO_CODE"])
sts = (values[ivi["state"] != "AUST"]
       .groupby(ivi.loc[ivi["state"] != "AUST", "ANZSCO_CODE"]).sum())
# find the biggest diff between national and sum of states 
gap = (nat.sort_index() - sts.sort_index()).abs().max().max()
assert gap < 1.0, f"states do not sum to AUST (max gap {gap:.2f})"
print(f"states vs AUST    : max gap {gap:.2f} ads (check passed)")


# seeding code snippet 
titles = (ivi.drop_duplicates("ANZSCO_CODE")
             .set_index("ANZSCO_CODE")["ANZSCO_TITLE"].to_dict())

occ_lines = [f"-- Seed: anzsco_occupation\n-- Source: {SOURCE}\n-- Rows: {len(titles)}\n",
             "INSERT INTO anzsco_occupation (code, title) VALUES"]
occ_lines.append(",\n".join(f"  ({q(c)}, {q(titles[c])})" for c in codes_needed))
occ_lines.append("ON CONFLICT (code) DO UPDATE SET title = EXCLUDED.title;\n")


# seed role_anzsco)mao
map_lines = [f"-- Seed: role_anzsco_map\n-- Team-built crosswalk, O*NET-based roles to ANZSCO 4-digit\n"
             f"-- Rows: {len(ROLE_TO_ANZSCO)}\n",
             "INSERT INTO role_anzsco_map (role_id, anzsco_code, confidence, rationale) VALUES"]
# join the value rows with a comma and newline 
map_lines.append(",\n".join(
    f"  ({q(r)}, {q(c)}, {q(conf)}, {q(why)})" # role, code, comfidence, reason
    for r, (c, conf, why) in sorted(ROLE_TO_ANZSCO.items())))
# we overwrite the role if already mapped 
map_lines.append("ON CONFLICT (role_id) DO UPDATE SET\n"
                 "  anzsco_code = EXCLUDED.anzsco_code,\n"
                 "  confidence  = EXCLUDED.confidence,\n"
                 "  rationale   = EXCLUDED.rationale;\n")

# seed vacancy_monthly 
rows = []                                                  # we will have (code, state, date , ads)
for _, r in ivi.iterrows():
    for m in month_cols: # loop over all the 246 months that is from 2006 to 2026 
        val = pd.to_numeric(r[m], errors="coerce")         # '.' (suppressed) becomes NaN
        if pd.notna(val):                                  # skip suppressed months
            rows.append((r["ANZSCO_CODE"], r["state"],
                         pd.Timestamp(m).strftime("%Y-%m-01"), round(float(val), 1))) # ad count rounded to one decimal place..

vac_lines = [f"-- Seed: vacancy_monthly\n-- Source: {SOURCE}\n-- Rows: {len(rows)}\n"]
BATCH = 1000                                               # rows per INSERT is fixed 

# step through 1000 rows 
for i in range(0, len(rows), BATCH):
    chunk = rows[i:i + BATCH]
    # join with comma and newline 
    vac_lines.append("INSERT INTO vacancy_monthly (anzsco_code, state, month, ads) VALUES")
    vac_lines.append(",\n".join(f"  ({q(c)}, {q(s)}, {q(d)}, {a})" for c, s, d, a in chunk))
    vac_lines.append("ON CONFLICT (anzsco_code, state, month) DO UPDATE SET ads = EXCLUDED.ads;\n")


# we create the output files 
os.makedirs(OUT_DIR, exist_ok=True)
for name, lines in [("seed_anzsco_occupation.sql", occ_lines),
                    ("seed_role_anzsco_map.sql", map_lines),
                    ("seed_vacancy_monthly.sql", vac_lines)]:
    with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

print(f"anzsco_occupation : {len(titles)} rows")
print(f"role_anzsco_map   : {len(ROLE_TO_ANZSCO)} rows")
print(f"vacancy_monthly   : {len(rows)} rows "
      f"({pd.Timestamp(min(month_cols)).strftime('%Y-%m')} to "
      f"{pd.Timestamp(max(month_cols)).strftime('%Y-%m')})")
print(f"written to        : {OUT_DIR}/")
