from internship_watcher.scrapers.workday import WorkdayScraper

BASE = "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"

# Shape mirrors a real Workday CXS jobPostings entry.
SAMPLE = {
    "title": "Robotics Research Intern - 2026",
    "externalPath": "/job/Switzerland-Zurich/Robotics-Research-Intern---2026_JR2014561",
    "locationsText": "Switzerland, Zurich",
    "postedOn": "Posted 30+ Days Ago",
    "bulletFields": ["JR2014561"],
}


class TestParsePosting:
    def test_parses_full_posting(self):
        listing = WorkdayScraper._parse_posting(SAMPLE, BASE, "NVIDIA")
        assert listing is not None
        assert listing.company == "NVIDIA"
        assert listing.title == "Robotics Research Intern - 2026"
        assert listing.location == "Switzerland, Zurich"
        assert listing.source == "workday"
        assert listing.external_id == "JR2014561"
        assert listing.url == BASE + SAMPLE["externalPath"]

    def test_base_url_trailing_slash_does_not_double(self):
        listing = WorkdayScraper._parse_posting(SAMPLE, BASE + "/", "NVIDIA")
        assert listing.url == BASE + SAMPLE["externalPath"]

    def test_falls_back_to_path_when_no_bullet_id(self):
        posting = {**SAMPLE, "bulletFields": []}
        listing = WorkdayScraper._parse_posting(posting, BASE, "NVIDIA")
        assert listing.external_id == SAMPLE["externalPath"]

    def test_returns_none_without_title_or_path(self):
        assert WorkdayScraper._parse_posting({"title": "x"}, BASE, "NVIDIA") is None
        assert (
            WorkdayScraper._parse_posting(
                {"externalPath": "/job/x"}, BASE, "NVIDIA"
            )
            is None
        )
