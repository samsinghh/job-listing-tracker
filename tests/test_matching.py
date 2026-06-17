from internship_watcher.matching import matches, normalize_title

MATCH = [
    "internship",
    "intern",
    "software engineer intern",
    "swe intern",
    "machine learning intern",
    "robotics intern",
    "summer 2027",
    "2027",
]
EXCLUDE = ["new grad", "full-time", "senior", "staff", "manager", "sales", "marketing"]


class TestNormalizeTitle:
    def test_lowercases_and_strips_punctuation(self):
        assert (
            normalize_title("Software Engineer Intern, Summer 2027 (Remote)")
            == "software engineer intern summer 2027 remote"
        )

    def test_collapses_whitespace(self):
        assert normalize_title("  SWE   Intern\t\n ") == "swe intern"

    def test_empty(self):
        assert normalize_title("") == ""
        assert normalize_title("   ") == ""


class TestMatches:
    def test_basic_intern_match(self):
        assert matches("Software Engineer Intern", MATCH, EXCLUDE)

    def test_phrase_keyword_match(self):
        assert matches("Machine Learning Intern, NYC", MATCH, EXCLUDE)

    def test_year_keyword_match(self):
        assert matches("Quant Trader — Summer 2027", MATCH, EXCLUDE)

    def test_no_match_when_no_keyword(self):
        assert not matches("Software Engineer", MATCH, EXCLUDE)

    def test_exclude_overrides_match(self):
        # Contains "intern" but also an excluded term.
        assert not matches("Senior Software Engineer Intern", MATCH, EXCLUDE)
        assert not matches("Full-Time Internship Program", MATCH, EXCLUDE)

    def test_word_boundary_avoids_substring_false_positive(self):
        # "internal" must NOT match the "intern" keyword.
        assert not matches("Internal Tools Engineer", MATCH, EXCLUDE)

    def test_empty_title_does_not_match(self):
        assert not matches("", MATCH, EXCLUDE)

    def test_case_insensitive(self):
        assert matches("SUMMER INTERNSHIP 2027", MATCH, EXCLUDE)
