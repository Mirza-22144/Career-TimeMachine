"""

WHAT THIS DOES
  Takes the raw O*NET Technology Skills export and turns it into a clean, deduplicated
  list of technologies relevant to IT roles 

FLOW
  raw CSV  ->  filter to IT occupations  
           ->  clean the names  and deduplicate

INPUT   data/raw/software_skills.csv       
OUTPUT  data/processed/skills_clean.csv     


"""

import csv                          # read/write CSV files 
import re                           # imports regex for cleaning
from collections import defaultdict # dictionary that creates empty values


RAW = "data/raw/software_skills.csv"          
OUT = "data/processed/skills_clean.csv"       # gives a clean csv file as output
SOURCE_LABEL = "O*NET Technology Skills 30.2" # proof where data is collected from


# we list all the soc codes here
IT_OCCUPATIONS = {                                   
    # all the software roles
    "15-1252.00": "Software Developers",
    "15-1251.00": "Computer Programmers",
    "15-1253.00": "Software Quality Assurance Analysts and Testers",
    "15-1254.00": "Web Developers",
    "15-1255.00": "Web and Digital Interface Designers",
    "15-1255.01": "Video Game Designers",
    "15-1299.08": "Computer Systems Engineers/Architects",
    # roles related to data
    "15-1242.00": "Database Administrators",
    "15-1243.00": "Database Architects",
    "15-1243.01": "Data Warehousing Specialists",
    "15-2051.00": "Data Scientists",
    "15-2051.01": "Business Intelligence Analysts",
    # infrastructure and network roles
    "15-1241.00": "Computer Network Architects",
    "15-1244.00": "Network and Computer Systems Administrators",
    "15-1231.00": "Computer Network Support Specialists",
    "15-1232.00": "Computer User Support Specialists",
    "15-1241.01": "Telecommunications Engineering Specialists",
    # security roles 
    "15-1212.00": "Information Security Analysts",
    "15-1299.04": "Penetration Testers",
    "15-1299.05": "Information Security Engineers",
    "15-1299.06": "Digital Forensics Analysts",
    # other tech roles
    "15-1211.00": "Computer Systems Analysts",
    "15-1221.00": "Computer and Information Research Scientists",
    "15-1299.01": "Web Administrators",
    "15-1299.07": "Blockchain Engineers",
    "15-1299.09": "Information Technology Project Managers",
    "11-3021.00": "Computer and Information Systems Managers",
}


# overrides the labels to clean familiar labels
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

# general rules for names ending in a filler noun
# also matches the whitespace 

TRAILING_NOISE = re.compile(
    r"\s+(software|tool|tools|systems?|programs?|applications?)$", re.I # makes it case insensitive
)


# the below function removes leading or trailing whitespaces 
def clean_label(raw: str) -> str:
    """Turn an O*NET Workplace Example into a readable name"""
    name = raw.strip()                # removes whitespaces         
    if name in OVERRIDES:                      # checks if an override is present then uses that
        return OVERRIDES[name]                
    name = TRAILING_NOISE.sub("", name).strip()  
    return OVERRIDES.get(name, name)         


# builds a snake_case id
def make_id(label: str) -> str:
    """Build a stable snake_case id taht is safe to use as a primary key """
    slug = label.lower()                                  
    slug = slug.replace("+", "plus")              # example c++ will become cplusplus         
    slug = slug.replace("#", "sharp")                 
    slug = slug.replace("&", "and")                        
    slug = re.sub(r"[^a-z0-9]+", "_", slug)                
    return slug.strip("_")[:64]                            

# main pipeline

def main():
    # we load the raw file
    with open(RAW, newline="", encoding="utf-8-sig") as f:
        all_rows = list(csv.DictReader(f))     # each row becomes a dict keyed by header

   # we filter the dataset based on IT occupations
    it_rows = [r for r in all_rows if r["O*NET-SOC Code"] in IT_OCCUPATIONS]

# we do not drop unflagged tech as our user might have used it before
    kept = it_rows

# UI SHOWS HOT AND IN DEMAND TECH FIRST AND THE REST REMAIN FINDABLE BY A SEARCH OPTION


# deduplicate
    merged = {}                      # single merged record
    occ_seen = defaultdict(set)     # set of occupations it appeared in
    cat_seen = defaultdict(set)    

    for r in kept:                                  
        label = clean_label(r["Workplace Example"])     # clean the name 
        sid = make_id(label)                        
        if not sid:                                  # here we skip if the id is empty    
            continue

       
        rec = merged.setdefault(sid, {
            "id": sid,
            "label": label,
            "category": r["Element Name"],              # O*NET's own grouping
            "hot_technology": False,                    # start false
            "in_demand": False,                         # start false
            "source": SOURCE_LABEL,
        })

       # we use the OR assign operator
        rec["hot_technology"] |= (r["Hot Technology"] == "Y")
        rec["in_demand"] |= (r["In Demand"] == "Y")

        # records when it was seen
        occ_seen[sid].add(IT_OCCUPATIONS[r["O*NET-SOC Code"]])
        cat_seen[sid].add(r["Element Name"])

  # write the output in a clean csv file
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([                                    # occurences and occupation are extra working data
            "id", "label", "category", "hot_technology", "in_demand",
            "source", "occurrences", "occupations",
        ])
        for sid in sorted(merged):                      # alphabetical by id
            rec = merged[sid]
            w.writerow([
                rec["id"],
                rec["label"],
                rec["category"],
                "true" if rec["hot_technology"] else "false",   # convert to lowercase for postgres
                "true" if rec["in_demand"] else "false",
                rec["source"],
                len(occ_seen[sid]),                     # how many occupations use it
                "; ".join(sorted(occ_seen[sid])),      
            ])

 # reports what happened 
    print(f"raw rows            : {len(all_rows):,}")
    print(f"IT occupation rows  : {len(it_rows):,}  ({len(IT_OCCUPATIONS)} occupations)")
    print(f"rows kept           : {len(kept):,}  (no flag filter applied)")
    print(f"unique skills out   : {len(merged):,}")
    print()
    demand = sum(1 for r in merged.values() if r["in_demand"])
    hot = sum(1 for r in merged.values() if r["hot_technology"])
    either = sum(1 for r in merged.values() if r["in_demand"] or r["hot_technology"])
    print(f"  In Demand         : {demand}")
    print(f"  Hot Technology    : {hot}")
    print(f"  either flag       : {either}   <- surface these first in the UI")
    print(f"  unflagged         : {len(merged) - either}   <- findable via search")
    print()
    print("Most widely used across occupations:")
    # sort by occupation count descending, show the top 15
    for sid in sorted(merged, key=lambda s: -len(occ_seen[s]))[:15]:
        print(f"  {len(occ_seen[sid]):2d}  {merged[sid]['label']}")
    print()
    print(f"written -> {OUT}")


if __name__ == "__main__":
    main()