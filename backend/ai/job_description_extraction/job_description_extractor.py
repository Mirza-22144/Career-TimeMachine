from __future__ import annotations

import html
import csv
import string

import os
import re
import json
import math
import unicodedata

from copy import deepcopy
from pathlib import Path
from collections import OrderedDict, defaultdict
from typing import (
    Any,
    Annotated,
    Callable,
    ClassVar,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Pattern,
    Sequence,
    Set,
    Tuple,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator
)

from gliner import GLiNER

try:
    from rapidfuzz import fuzz, process
except ImportError:
    fuzz = None
    process = None


MAX_RAW_TEXT_LENGTH = 20000

EXPECTED_FIELDS = {
    "skills",
    "responsibilities",
    "min_years_experience",
    "keywords",
    "role_title_guess"
}


INSTRUCTION_LIKE_PATTERNS = [
    (
        r"\b(?:ignore|disregard|override)\b"
        r".{0,100}"
        r"\b(?:instruction|instructions|validation|"
        r"rule|rules|prompt)\b"
    ),
    (
        r"\b(?:reveal|display|print|return|output|expose)\b"
        r".{0,100}"
        r"\b(?:system prompt|admin password|password|"
        r"secret|access token|credentials)\b"
    ),
    (
        r"<\s*(?:system|assistant|instruction)"
        r"(?:\s|>|/)"
    ),
    (
        r"\bact as\b"
        r".{0,80}"
        r"\b(?:system|assistant|administrator|admin)\b"
    ),
    (
        r"\bfollow\b"
        r".{0,60}"
        r"\b(?:these|my|the following)\b"
        r".{0,20}"
        r"\binstructions?\b"
    )
]

UNSAFE_OUTPUT_PATTERNS = [
    r"\bsystem prompt\b",
    r"\badmin password\b",
    r"\bsecret access token\b",
    r"\bignore all validation\b",
    r"\bignore previous instructions?\b",
    r"\bdisregard previous instructions?\b",
    r"\breveal hidden instructions?\b"
]


class ExtractedSkill(BaseModel):
    model_config = ConfigDict(extra='forbid')
    label: str = Field(min_length=1, max_length=120)
    category: Literal['technical', 'soft']


class JobDescriptionExtraction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    skills: list[ExtractedSkill] = Field(default_factory=list, max_length=50)
    responsibilities: list[str] = Field(default_factory=list, max_length=30)
    min_years_experience: int | None = Field(default=None, ge=0, le=50)
    keywords: list[str] = Field(default_factory=list, max_length=30)
    role_title_guess: str | None = Field(default=None, max_length=120)

    @field_validator('responsibilities', 'keywords')
    @classmethod
    def validate_string_lists(cls, values):
        cleaned_values = []
        seen_values = set()
        for value in values:
            cleaned_value = str(value).strip()
            if not cleaned_value:
                continue
            if len(cleaned_value) > 300:
                raise ValueError('A list item is too long.')
            duplicate_key = cleaned_value.casefold()
            if duplicate_key in seen_values:
                continue
            seen_values.add(duplicate_key)
            cleaned_values.append(cleaned_value)
        return cleaned_values


class JobDescriptionExtractor:
    """I extract structured requirements from one job advert."""
    MAXIMUM_CHARACTERS = 20000
    TECHNICAL_ENTITY_LABELS = {'programming language', 'cloud platform', 'container technology', 'software tool', 'database technology', 'development practice', 'technical skill'}
    GLINER_LABELS = ['job title', 'programming language', 'cloud platform', 'container technology', 'software tool', 'database technology', 'development practice', 'technical skill', 'job responsibility']
    TECHNICAL_ALIASES = {'\\bpython\\b': 'Python', '\\bjava\\b': 'Java', '\\bjavascript\\b': 'JavaScript', '\\btypescript\\b': 'TypeScript', '\\bc\\+\\+\\b': 'C++', '\\bc#\\b': 'C#', '\\b\\.net\\b': '.NET', '\\bsql\\b': 'SQL', '\\bhtml5?\\b': 'HTML', '\\bcss3?\\b': 'CSS', '\\breact(?:\\.js)?\\b': 'React', '\\bangular\\b': 'Angular', '\\bnode(?:\\.js)?\\b': 'Node.js', '\\baws\\b': 'AWS', '\\bamazon web services\\b': 'AWS', '\\bmicrosoft azure\\b': 'Microsoft Azure', '\\bazure\\b': 'Microsoft Azure', '\\bgoogle cloud platform\\b': 'Google Cloud Platform', '\\bgcp\\b': 'Google Cloud Platform', '\\bdocker\\b': 'Docker', '\\bkubernetes\\b': 'Kubernetes', '\\bci\\s*/\\s*cd\\b': 'CI/CD', '\\bcontinuous integration\\b': 'Continuous integration', '\\bcontinuous deployment\\b': 'Continuous deployment', '\\bgit\\b': 'Git', '\\bgithub\\b': 'GitHub', '\\bgithub actions\\b': 'GitHub Actions', '\\blinux\\b': 'Linux', '\\bwindows server\\b': 'Windows Server', '\\brest(?:ful)? apis?\\b': 'REST APIs', '\\bgraphql\\b': 'GraphQL', '\\bpostgresql\\b': 'PostgreSQL', '\\bmysql\\b': 'MySQL', '\\bmongodb\\b': 'MongoDB', '\\bsnowflake\\b': 'Snowflake', '\\btableau\\b': 'Tableau', '\\bpower bi\\b': 'Power BI', '\\blook(?:er)? studio\\b': 'Looker Studio', '\\bapache spark\\b': 'Apache Spark', '\\bspark\\b': 'Apache Spark', '\\bhadoop\\b': 'Apache Hadoop', '\\btensorflow\\b': 'TensorFlow', '\\bpytorch\\b': 'PyTorch', '\\bscikit-learn\\b': 'scikit-learn', '\\bmachine learning\\b': 'Machine learning', '\\bdata visuali[sz]ation\\b': 'Data visualisation', '\\bfigma\\b': 'Figma', '\\bjira\\b': 'Jira', '\\bsalesforce\\b': 'Salesforce', '\\bterraform\\b': 'Terraform', '\\bansible\\b': 'Ansible', '\\bagile\\b': 'Agile', '\\bscrum\\b': 'Scrum'}
    SOFT_SKILL_ALIASES = {'\\bstakeholder communication\\b': 'Stakeholder communication', '\\bcommunicat(?:e|es|ing|ion)\\b': 'Communication', '\\bmentor(?:ing|ed|s)?\\b': 'Mentoring', '\\bleadership\\b': 'Leadership', '\\blead(?:ing|s)?\\s+(?:a|the|our)?\\s*team\\b': 'Leadership', '\\bcollaborat(?:e|es|ed|ing|ion)\\b': 'Collaboration', '\\bteamwork\\b': 'Teamwork', '\\bteam player\\b': 'Teamwork', '\\bproblem[- ]solving\\b': 'Problem solving', '\\bcritical thinking\\b': 'Critical thinking', '\\btime management\\b': 'Time management', '\\bprioriti[sz](?:e|es|ed|ing|ation)\\b': 'Prioritisation', '\\badaptab(?:ility|le)\\b': 'Adaptability', '\\battention to detail\\b': 'Attention to detail', '\\bconflict resolution\\b': 'Conflict resolution', '\\bdecision[- ]making\\b': 'Decision making', '\\bpresentation skills?\\b': 'Presentation', '\\bnegotiat(?:e|es|ed|ing|ion)\\b': 'Negotiation', '\\binterpersonal skills?\\b': 'Interpersonal communication', '\\bwritten communication\\b': 'Written communication', '\\bverbal communication\\b': 'Verbal communication'}
    RESPONSIBILITY_VERBS = ['analyse', 'analyze', 'architect', 'build', 'collaborate', 'communicate', 'configure', 'coordinate', 'create', 'debug', 'deliver', 'deploy', 'design', 'develop', 'document', 'ensure', 'evaluate', 'implement', 'lead', 'maintain', 'manage', 'mentor', 'monitor', 'optimise', 'optimize', 'own', 'plan', 'review', 'secure', 'support', 'test', 'train', 'troubleshoot', 'work with']
    GENERIC_TECHNICAL_TERMS = {'code', 'services', 'software', 'technology', 'technical skill', 'software development experience', 'junior engineers', 'product stakeholders'}
    NUMBER_WORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20}

    def __init__(self, model, catalogue_file):
        self.model = model
        self.catalogue_file = Path(catalogue_file)
        with open(self.catalogue_file, 'r', encoding='utf-8') as file:
            catalogue_payload = json.load(file)
        self.catalogue_skills = catalogue_payload['skills']

    def extract(self, raw_text: str) -> dict:
        """I return exactly the five required fields."""
        cleaned_text = self._clean_input(raw_text)
        model_entities = self._extract_model_entities(cleaned_text)
        technical_skills = self._extract_technical_skills(cleaned_text, model_entities)
        soft_skills = self._extract_soft_skills(cleaned_text)
        skills = [{'label': label, 'category': 'technical'} for label in technical_skills]
        skills.extend([{'label': label, 'category': 'soft'} for label in soft_skills])
        responsibilities = self._extract_responsibilities(cleaned_text)
        role_title_guess = self._extract_role_title(cleaned_text, model_entities)
        min_years_experience = self._extract_minimum_experience(cleaned_text)
        keywords = self._build_keywords(technical_skills, soft_skills, role_title_guess)
        validated_output = JobDescriptionExtraction.model_validate({'skills': skills, 'responsibilities': responsibilities, 'min_years_experience': min_years_experience, 'keywords': keywords, 'role_title_guess': role_title_guess})
        return validated_output.model_dump()

    def _clean_input(self, raw_text):
        if not isinstance(raw_text, str):
            raise TypeError('raw_text must be a string.')
        if len(raw_text) > self.MAXIMUM_CHARACTERS:
            raise ValueError('raw_text exceeds the 20,000-character limit.')
        cleaned_text = html.unescape(raw_text)
        cleaned_text = unicodedata.normalize('NFKC', cleaned_text)
        cleaned_text = ''.join((character for character in cleaned_text if character in '\n\t' or not unicodedata.category(character).startswith('C')))
        cleaned_text = re.sub('[ \\t]+', ' ', cleaned_text)
        cleaned_text = re.sub('\\n{3,}', '\n\n', cleaned_text)
        cleaned_text = cleaned_text.strip()
        if not cleaned_text:
            raise ValueError('raw_text cannot be empty.')
        return cleaned_text

    def _build_chunks(self, text, maximum_characters=1500):
        paragraphs = [paragraph.strip() for paragraph in re.split('\\n+', text) if paragraph.strip()]
        chunks = []
        current_chunk = ''
        for paragraph in paragraphs:
            proposed_chunk = paragraph if not current_chunk else current_chunk + '\n' + paragraph
            if len(proposed_chunk) <= maximum_characters:
                current_chunk = proposed_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(paragraph) <= maximum_characters:
                    current_chunk = paragraph
                else:
                    for position in range(0, len(paragraph), maximum_characters):
                        chunks.append(paragraph[position:position + maximum_characters])
                    current_chunk = ''
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def _extract_model_entities(self, text):
        all_entities = []
        for chunk in self._build_chunks(text):
            entities = self.model.predict_entities(chunk, self.GLINER_LABELS, threshold=0.35)
            for entity in entities:
                all_entities.append({'text': str(entity.get('text', '')).replace('\n', ' ').strip(), 'label': str(entity.get('label', '')), 'score': float(entity.get('score', 0.0))})
        return all_entities

    def _extract_technical_skills(self, text, model_entities):
        found_skills = []
        seen_skills = set()

        def add_skill(label):
            cleaned_label = str(label).strip()
            duplicate_key = cleaned_label.casefold()
            if not cleaned_label or duplicate_key in seen_skills:
                return
            seen_skills.add(duplicate_key)
            found_skills.append(cleaned_label)
        for pattern, canonical_label in self.TECHNICAL_ALIASES.items():
            if re.search(pattern, text, flags=re.IGNORECASE):
                add_skill(canonical_label)
        normalised_text = text.casefold()
        for record in self.catalogue_skills:
            catalogue_label = record['label'].strip()
            searchable_label = catalogue_label.casefold()
            if len(re.sub('[^a-z0-9]', '', searchable_label)) < 3:
                continue
            match_pattern = '(?<![a-z0-9])' + re.escape(searchable_label) + '(?![a-z0-9])'
            if re.search(match_pattern, normalised_text):
                add_skill(catalogue_label)
        for entity in model_entities:
            if entity['label'] not in self.TECHNICAL_ENTITY_LABELS:
                continue
            if entity['score'] < 0.65:
                continue
            candidate = entity['text'].strip(' ,.;:-')
            if candidate.casefold() in self.GENERIC_TECHNICAL_TERMS:
                continue
            if len(candidate) < 2:
                continue
            add_skill(candidate)
        return found_skills[:30]

    def _extract_soft_skills(self, text):
        found_skills = []
        seen_skills = set()
        for pattern, canonical_label in self.SOFT_SKILL_ALIASES.items():
            if not re.search(pattern, text, flags=re.IGNORECASE):
                continue
            duplicate_key = canonical_label.casefold()
            if duplicate_key in seen_skills:
                continue
            seen_skills.add(duplicate_key)
            found_skills.append(canonical_label)
        return found_skills[:20]

    def _extract_responsibilities(self, text):
        verb_expression = '|'.join(sorted((re.escape(verb) for verb in self.RESPONSIBILITY_VERBS), key=len, reverse=True))
        verb_pattern = re.compile(f'\\b(?:{verb_expression})\\b', flags=re.IGNORECASE)
        sentences = [sentence.strip() for sentence in re.split('(?<=[.!?])\\s+|\\n+', text) if sentence.strip()]
        responsibilities = []
        seen_responsibilities = set()
        for sentence in sentences:
            sentence_matches = list(verb_pattern.finditer(sentence))
            if not sentence_matches:
                continue
            for index, match in enumerate(sentence_matches):
                start_position = match.start()
                if index + 1 < len(sentence_matches):
                    end_position = sentence_matches[index + 1].start()
                else:
                    end_position = len(sentence)
                responsibility = sentence[start_position:end_position].strip(' ,;:-')
                responsibility = re.sub('\\s+', ' ', responsibility)
                responsibility = re.sub('\\band\\s*$', '', responsibility, flags=re.IGNORECASE).strip()
                if not 5 <= len(responsibility) <= 300:
                    continue
                responsibility = responsibility[0].upper() + responsibility[1:]
                duplicate_key = responsibility.casefold()
                if duplicate_key in seen_responsibilities:
                    continue
                seen_responsibilities.add(duplicate_key)
                responsibilities.append(responsibility)
        return responsibilities[:30]

    def _extract_role_title(self, text, model_entities):
        title_candidates = [entity for entity in model_entities if entity['label'] == 'job title' and entity['score'] >= 0.65]
        if title_candidates:
            best_candidate = max(title_candidates, key=lambda item: item['score'])
            return best_candidate['text'].strip(' ,.;:-')[:120]
        first_line = text.splitlines()[0].strip()
        first_line_words = first_line.split()
        if 1 <= len(first_line_words) <= 10 and len(first_line) <= 120:
            return first_line
        return None

    def _number_to_integer(self, value):
        normalised_value = str(value).strip().casefold()
        if normalised_value.isdigit():
            return int(normalised_value)
        return self.NUMBER_WORDS.get(normalised_value)

    def _extract_minimum_experience(self, text):
        number_expression = '(?:\\d{1,2}|' + '|'.join(self.NUMBER_WORDS.keys()) + ')'
        experience_pattern = re.compile(f'\n            (?:\n                minimum\\s+(?:of\\s+)?\n                |\n                at\\s+least\\s+\n                |\n                more\\s+than\\s+\n                |\n                over\\s+\n            )?\n            (?P<minimum>{number_expression})\n            \\s*\n            (?:\n                \\+\n                |\n                [-–]\\s*\n                (?P<maximum>{number_expression})\n                |\n                \\s+or\\s+(?:more|above)\n            )?\n            \\s+\n            years?\n            (?:\n                \\s+of\n                [^.;,\\n]{{0,60}}\n                experience\n                |\n                \\s+experience\n            )?\n            ', flags=re.IGNORECASE | re.VERBOSE)
        candidates = []
        for match in experience_pattern.finditer(text):
            context_start = max(0, match.start() - 60)
            context_end = min(len(text), match.end() + 80)
            context = text[context_start:context_end].casefold()
            requirement_signals = {'experience', 'minimum', 'at least', 'required', 'requirement', 'candidate', 'applicant', 'seeking', 'must have', 'you have', 'you will have'}
            if not any((signal in context for signal in requirement_signals)):
                continue
            minimum_value = self._number_to_integer(match.group('minimum'))
            if minimum_value is not None and 0 <= minimum_value <= 50:
                candidates.append(minimum_value)
        if not candidates:
            return None
        return min(candidates)

    def _build_keywords(self, technical_skills, soft_skills, role_title_guess):
        keywords = []
        seen_keywords = set()
        for keyword in [*technical_skills, *soft_skills]:
            duplicate_key = keyword.casefold()
            if duplicate_key in seen_keywords:
                continue
            seen_keywords.add(duplicate_key)
            keywords.append(keyword)
        return keywords[:30]


class TunedJobDescriptionExtractor:
    """
    I improve the hybrid extractor using validation-set
    error analysis while preserving the backend contract.
    """
    OUTPUT_FIELDS = {'skills', 'responsibilities', 'min_years_experience', 'keywords', 'role_title_guess'}
    RESPONSIBILITY_VERBS = ['administer', 'analyse', 'analyze', 'build', 'collaborate', 'communicate', 'configure', 'coordinate', 'create', 'deploy', 'design', 'develop', 'document', 'evaluate', 'facilitate', 'implement', 'investigate', 'lead', 'maintain', 'manage', 'mentor', 'monitor', 'negotiate', 'optimise', 'optimize', 'plan', 'present', 'prioritise', 'prioritize', 'review', 'secure', 'support', 'test', 'troubleshoot', 'work']
    SOFT_SKILL_RULES = [('\\battention[\\s-]+to[\\s-]+detail\\b', 'Attention to detail'), ('\\bcritical[\\s-]+thinking\\b', 'Critical thinking'), ('\\bproblem[\\s-]+solving\\b|\\btroubleshoot\\w*\\b', 'Problem solving'), ('\\bcollaborat(?:e|es|ed|ing|ion|ive)\\b|\\bteamwork\\b', 'Collaboration'), ('\\bstakeholder(?:s)?\\b.{0,45}\\bcommunicat\\w*\\b|\\bcommunicat\\w*\\b.{0,45}\\bstakeholder(?:s)?\\b', 'Stakeholder communication'), ('\\bpresent(?:s|ed|ing|ation|ations)?\\b', 'Presentation'), ('\\bleadership\\b|\\blead(?:s|ing)?\\b', 'Leadership')]
    TECHNICAL_NOISE_PATTERNS = ['^practical knowledge$', '^analytics experience$', '^web[\\s-]+development experience$', '^interface[\\s-]+design experience$', '^software development experience$', '^problem[\\s-]+solving skills?$']
    TECHNICAL_NORMALISATION = {'machine-learning models': 'Machine learning', 'machine learning models': 'Machine learning', 'machine-learning': 'Machine learning', 'ci/cd pipelines': 'CI/CD', 'cicd pipelines': 'CI/CD'}
    ROLE_TITLE_TERMS = {'administrator', 'analyst', 'architect', 'developer', 'designer', 'engineer', 'manager', 'programmer', 'scientist', 'specialist', 'tester'}

    def __init__(self, base_extractor):
        self.base_extractor = base_extractor

    @staticmethod
    def _normalise_comparison_text(value):
        return re.sub('[^a-z0-9+#./]+', ' ', str(value).lower()).strip()

    def _deduplicate_items(self, values):
        accepted = []
        seen = set()
        for value in values:
            cleaned_value = re.sub('\\s+', ' ', str(value)).strip(' \t\r\n,;:.-')
            comparison_value = self._normalise_comparison_text(cleaned_value)
            if cleaned_value and comparison_value not in seen:
                seen.add(comparison_value)
                accepted.append(cleaned_value)
        return accepted

    def _correct_skills(self, raw_text, original_skills):
        technical_skills = []
        soft_skills = []
        for skill in original_skills:
            label = str(skill.get('label', '')).strip()
            category = str(skill.get('category', '')).strip().lower()
            if not label:
                continue
            normalised_label = self._normalise_comparison_text(label)
            replacement = self.TECHNICAL_NORMALISATION.get(normalised_label, label)
            is_noise = any((re.fullmatch(pattern, normalised_label, flags=re.IGNORECASE) for pattern in self.TECHNICAL_NOISE_PATTERNS))
            soft_match = None
            for pattern, soft_label in self.SOFT_SKILL_RULES:
                if re.search(pattern, label, flags=re.IGNORECASE):
                    soft_match = soft_label
                    break
            if soft_match:
                soft_skills.append(soft_match)
            elif category == 'technical' and (not is_noise):
                technical_skills.append(replacement)
            elif category == 'soft':
                soft_skills.append(label)
        for pattern, soft_label in self.SOFT_SKILL_RULES:
            if re.search(pattern, raw_text, flags=re.IGNORECASE | re.DOTALL):
                soft_skills.append(soft_label)
        technical_skills = self._deduplicate_items(technical_skills)
        soft_skills = self._deduplicate_items(soft_skills)
        corrected_skills = []
        for label in technical_skills:
            corrected_skills.append({'label': label, 'category': 'technical'})
        for label in soft_skills:
            corrected_skills.append({'label': label, 'category': 'soft'})
        return corrected_skills

    def _is_responsibility_clause(self, clause):
        comparison_clause = clause.lower().strip()
        non_action_openings = ['design experience', 'design systems', 'development experience', 'practical knowledge']
        if any((comparison_clause.startswith(opening) for opening in non_action_openings)):
            return False
        verb_pattern = '^(?:' + '|'.join((re.escape(verb) for verb in self.RESPONSIBILITY_VERBS)) + ')\\b'
        return bool(re.search(verb_pattern, comparison_clause, flags=re.IGNORECASE))

    def _extract_corrected_responsibilities(self, raw_text, original_responsibilities):
        working_text = str(raw_text).replace('\r\n', '\n').replace('\r', '\n')
        action_pattern = '(?:' + '|'.join((re.escape(verb) for verb in self.RESPONSIBILITY_VERBS)) + ')'
        working_text = re.sub(f'\\n+\\s*(?={action_pattern}\\b)', ' || ', working_text, flags=re.IGNORECASE)
        working_text = re.sub('\\s*\\n+\\s*', ' ', working_text)
        working_text = re.sub('[•●▪►]+', ' || ', working_text)
        initial_segments = re.split('\\s*(?:\\|\\||;|(?<=[.!?]))\\s+', working_text)
        candidate_clauses = []
        for segment in initial_segments:
            segment = re.sub('^[\\-\\*\\u2022]+\\s*', '', segment).strip(' \t\r\n.;:')
            if not segment:
                continue
            parts = re.split(f',\\s*(?={action_pattern}\\b)', segment, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip(' \t\r\n,.;:')
                if self._is_responsibility_clause(part):
                    candidate_clauses.append(part[0].upper() + part[1:])
        candidate_clauses = self._deduplicate_items(candidate_clauses)
        if not candidate_clauses:
            candidate_clauses = self._deduplicate_items(original_responsibilities)
        return candidate_clauses[:12]

    def _correct_role_title(self, raw_text, original_title):
        non_empty_lines = [re.sub('\\s+', ' ', line).strip() for line in str(raw_text).splitlines() if line.strip()]
        if not non_empty_lines:
            return original_title
        first_line = non_empty_lines[0]
        first_line_words = first_line.split()
        contains_role_term = any((re.search(f'\\b{re.escape(term)}\\b', first_line, flags=re.IGNORECASE) for term in self.ROLE_TITLE_TERMS))
        looks_like_sentence = bool(re.search('[.!?]$', first_line))
        if 1 < len(first_line_words) <= 10 and contains_role_term and (not looks_like_sentence):
            original_normalised = self._normalise_comparison_text(original_title or '')
            heading_normalised = self._normalise_comparison_text(first_line)
            if not original_normalised or original_normalised in heading_normalised:
                return first_line
        return original_title

    def extract(self, raw_text):
        original_result = self.base_extractor.extract(raw_text)
        corrected_result = deepcopy(original_result)
        corrected_result['skills'] = self._correct_skills(raw_text, original_result.get('skills', []))
        corrected_result['responsibilities'] = self._extract_corrected_responsibilities(raw_text, original_result.get('responsibilities', []))
        corrected_result['role_title_guess'] = self._correct_role_title(raw_text, original_result.get('role_title_guess'))
        corrected_result['keywords'] = self._deduplicate_items([skill['label'] for skill in corrected_result['skills']])
        if set(corrected_result.keys()) != self.OUTPUT_FIELDS:
            raise ValueError('I require exactly the five agreed backend output fields.')
        return corrected_result


def contains_instruction_pattern(value):
    value = str(value)
    return any((re.search(pattern, value, flags=re.IGNORECASE | re.DOTALL) for pattern in INSTRUCTION_LIKE_PATTERNS))


def remove_instruction_like_segments(raw_text):
    """
    I remove suspicious instruction-like segments while
    retaining ordinary job requirements and duties.
    """
    segments = re.split('(?<=[.!?])\\s+|\\n+', raw_text)
    accepted_segments = []
    removed_segments = []
    for segment in segments:
        cleaned_segment = segment.strip()
        if not cleaned_segment:
            continue
        if contains_instruction_pattern(cleaned_segment):
            removed_segments.append(cleaned_segment)
        else:
            accepted_segments.append(cleaned_segment)
    sanitised_text = '\n'.join(accepted_segments).strip()
    return (sanitised_text, removed_segments)


def preserve_original_responsibilities(self, raw_text, original_responsibilities):
    """
    I retain the validated responsibility results produced
    by my original hybrid extraction pipeline.
    """
    cleaned_responsibilities = []
    for responsibility in original_responsibilities:
        cleaned_value = ' '.join(str(responsibility).split()).strip(' \t\r\n,.;:')
        if cleaned_value:
            cleaned_responsibilities.append(cleaned_value)
    return self._deduplicate_items(cleaned_responsibilities)[:12]


def validate_output_contract(output):
    """
    I independently validate the five-field AI contract.
    """
    errors = []
    if not isinstance(output, dict):
        return ['The output is not a dictionary.']
    if set(output.keys()) != EXPECTED_FIELDS:
        errors.append('The output does not contain exactly the five required fields.')
    if not isinstance(output.get('skills'), list):
        errors.append('The skills field is not a list.')
    else:
        for index, skill in enumerate(output['skills']):
            if not isinstance(skill, dict):
                errors.append(f'Skill {index} is not an object.')
                continue
            if set(skill.keys()) != {'label', 'category'}:
                errors.append(f'Skill {index} has invalid fields.')
            if not isinstance(skill.get('label'), str):
                errors.append(f'Skill {index} has an invalid label.')
            if skill.get('category') not in {'technical', 'soft'}:
                errors.append(f'Skill {index} has an invalid category.')
    if not isinstance(output.get('responsibilities'), list):
        errors.append('The responsibilities field is not a list.')
    elif not all((isinstance(item, str) for item in output['responsibilities'])):
        errors.append('A responsibility is not a string.')
    experience = output.get('min_years_experience')
    if not (experience is None or (isinstance(experience, int) and (not isinstance(experience, bool)) and (experience >= 0))):
        errors.append('The minimum experience field is invalid.')
    if not isinstance(output.get('keywords'), list):
        errors.append('The keywords field is not a list.')
    elif not all((isinstance(item, str) for item in output['keywords'])):
        errors.append('A keyword is not a string.')
    role_title = output.get('role_title_guess')
    if not (role_title is None or isinstance(role_title, str)):
        errors.append('The role title is invalid.')
    return errors


def secure_extract(self, raw_text):
    """
    I treat the supplied job advert as untrusted text,
    remove instruction-like segments and validate the
    structured result before returning it.
    """
    if not isinstance(raw_text, str):
        return extract_before_security_filter(self, raw_text)
    if len(raw_text) > MAX_RAW_TEXT_LENGTH:
        return extract_before_security_filter(self, raw_text)
    sanitised_text, removed_segments = remove_instruction_like_segments(raw_text)
    if not sanitised_text.strip():
        raise ValueError('I cannot extract a job description after removing instruction-like content.')
    result = extract_before_security_filter(self, sanitised_text)
    secured_result = deepcopy(result)
    secured_result['skills'] = [skill for skill in secured_result['skills'] if not contains_unsafe_output(skill.get('label', ''))]
    secured_result['responsibilities'] = [responsibility for responsibility in secured_result['responsibilities'] if not contains_unsafe_output(responsibility)]
    secured_result['keywords'] = self._deduplicate_items([skill['label'] for skill in secured_result['skills']])
    if contains_unsafe_output(secured_result.get('role_title_guess', '')):
        secured_result['role_title_guess'] = None
    contract_errors = validate_output_contract(secured_result)
    if contract_errors:
        raise ValueError('I rejected an invalid secured output: ' + '; '.join(contract_errors))
    return secured_result


def contains_unsafe_output(value):
    value = str(value)
    return any((re.search(pattern, value, flags=re.IGNORECASE) for pattern in UNSAFE_OUTPUT_PATTERNS))


# I retain the selected original responsibility component.
TunedJobDescriptionExtractor._extract_corrected_responsibilities = (
    preserve_original_responsibilities
)

# I apply the final security wrapper.
extract_before_security_filter = (
    TunedJobDescriptionExtractor.extract
)

TunedJobDescriptionExtractor.extract = secure_extract


def load_extractor(
    model_directory,
    catalogue_file
):
    """
    I load the local GLiNER model once and return an
    extractor exposing extract(raw_text: str) -> dict.
    """

    local_model = GLiNER.from_pretrained(
        str(model_directory),
        local_files_only=True
    )

    base_extractor = JobDescriptionExtractor(
        model=local_model,
        catalogue_file=str(catalogue_file)
    )

    return TunedJobDescriptionExtractor(
        base_extractor
    )
