"""The extraction model's broad labels also tag ordinary phrases. Those must
not be listed as technical skills; real technologies still are."""

from pathlib import Path

from app.ml.job_description_extraction.job_description_extractor import JobDescriptionExtractor

CATALOGUE = Path(__file__).resolve().parent.parent / "app" / "ml" / "job_description_extraction" / "skill_catalogue.json"


def _entity(text, label, score=0.9):
    return {"text": text, "label": label, "score": score}


def _technical(entities, text=""):
    # No model needed: the entities are passed in.
    return JobDescriptionExtractor(model=None, catalogue_file=CATALOGUE)._extract_technical_skills(text, entities)


def test_ordinary_phrases_are_not_technical_skills():
    found = _technical(
        [
            _entity("backend development experience", "technical skill"),
            _entity("non-technical users", "technical skill"),
            _entity("communication skills", "technical skill"),
            _entity("incident reviews", "development practice"),
            _entity("release process", "development practice"),
            _entity("agile delivery", "development practice"),
            _entity("Salesforce-powered", "software tool"),
            _entity("user-first approach", "development practice"),
            _entity("Solution Design Services Programme", "software tool"),
            _entity("hybrid", "cloud platform"),
            _entity("checkout", "cloud platform"),
        ]
    )

    assert found == []


def test_real_technologies_are_kept():
    found = _technical(
        [
            _entity("containers", "container technology"),
            _entity("cloud platforms", "cloud platform"),
            _entity("SQL databases", "database technology"),
            _entity("Intune", "software tool"),
            _entity("automated testing", "development practice"),
        ],
        text="We use Python and Git.",
    )

    assert {"Python", "Git", "containers", "cloud platforms", "SQL databases", "Intune", "automated testing"} <= set(found)
