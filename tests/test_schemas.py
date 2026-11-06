from src.schemas.ticket import Category, Priority


def test_category_taxonomy_has_other_fallback() -> None:
    assert Category("other") is Category.OTHER


def test_priority_values() -> None:
    assert [p.value for p in Priority] == ["low", "medium", "high", "urgent"]
