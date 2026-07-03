from app.models.catalog import CatalogEntry
from app.models.requirements import HiringRequirements
from app.services.candidate_retriever import CandidateRetriever


class StubCatalogLoader:
    def __init__(self, entries: list[CatalogEntry]) -> None:
        self._catalog = entries

    @property
    def catalog(self) -> list[CatalogEntry]:
        return self._catalog


def make_entry(entity_id: str, name: str, description: str, *, skills: list[str] | None = None, job_levels: list[str] | None = None, target_industries: list[str] | None = None, primary_function: str | None = None) -> CatalogEntry:
    return CatalogEntry(
        entity_id=entity_id,
        name=name,
        link="https://example.com/assessment",
        description=description,
        skills=skills or [],
        job_levels=job_levels or [],
        target_industries=target_industries or [],
        primary_function=primary_function,
    )


def test_retrieves_candidates_with_metadata_and_keyword_overlap() -> None:
    entry_one = make_entry(
        "1",
        "Senior Software Engineer Assessment",
        "Measures Python programming and leadership skills.",
        skills=["python"],
        job_levels=["Senior", "Manager"],
        target_industries=["finance"],
        primary_function="software engineering",
    )
    entry_two = make_entry(
        "2",
        "Finance Operations Test",
        "Covers finance workflow and operations.",
        skills=["excel"],
        job_levels=["Entry-Level"],
        target_industries=["finance"],
        primary_function="operations",
    )

    retriever = CandidateRetriever(StubCatalogLoader([entry_one, entry_two]))
    requirements = HiringRequirements(
        role="software engineer",
        seniority="senior",
        technical_skills=["python"],
        industry="finance",
    )

    results = retriever.retrieve(requirements)

    assert [entry.entity_id for entry in results] == ["1"]


def test_fuzzy_matching_matches_similar_role_names() -> None:
    entry = make_entry(
        "3",
        "Software Engineering Fundamentals",
        "Used for evaluating engineering practice and delivery.",
        skills=["java"],
        job_levels=["Mid-Professional"],
    )
    retriever = CandidateRetriever(StubCatalogLoader([entry]))
    requirements = HiringRequirements(role="software engineer", technical_skills=["java"])

    results = retriever.retrieve(requirements)

    assert [entry.entity_id for entry in results] == ["3"]


def test_returns_empty_when_no_candidate_matches() -> None:
    entry = make_entry(
        "4",
        "Recruitment Operations Assessment",
        "Focused on hiring workflows.",
        skills=["recruiting"],
    )
    retriever = CandidateRetriever(StubCatalogLoader([entry]))
    requirements = HiringRequirements(role="software engineer", technical_skills=["python"])

    results = retriever.retrieve(requirements)

    assert results == []


def test_preserves_catalog_order_for_matching_candidates() -> None:
    first = make_entry(
        "5",
        "Python Developer Assessment",
        "Covers Python and software development.",
        skills=["python"],
        job_levels=["Mid-Professional"],
    )
    second = make_entry(
        "6",
        "Software Engineering Practice",
        "Covers engineering practice and Python.",
        skills=["python"],
        job_levels=["Senior"],
    )

    retriever = CandidateRetriever(StubCatalogLoader([first, second]))
    requirements = HiringRequirements(role="software engineer", technical_skills=["python"])

    results = retriever.retrieve(requirements)

    assert [entry.entity_id for entry in results] == ["5", "6"]
