from internship_watcher.db import dedup_key
from internship_watcher.matching import normalize_url


class TestNormalizeUrl:
    def test_drops_query_and_fragment(self):
        assert (
            normalize_url("https://x.com/jobs/1?gh_src=abc#top")
            == "https://x.com/jobs/1"
        )

    def test_strips_trailing_slash_and_lowercases_host(self):
        assert normalize_url("https://X.com/Jobs/1/") == "https://x.com/Jobs/1"


class TestDedupKey:
    def test_stable_for_equivalent_inputs(self):
        a = dedup_key("Anthropic", "Software Engineer Intern", "https://x.com/jobs/1")
        b = dedup_key(
            "anthropic",
            "Software   Engineer Intern!",
            "https://x.com/jobs/1?utm=foo",
        )
        assert a == b

    def test_differs_on_different_title(self):
        a = dedup_key("Anthropic", "SWE Intern", "https://x.com/jobs/1")
        b = dedup_key("Anthropic", "ML Intern", "https://x.com/jobs/1")
        assert a != b

    def test_differs_on_different_url(self):
        a = dedup_key("Anthropic", "SWE Intern", "https://x.com/jobs/1")
        b = dedup_key("Anthropic", "SWE Intern", "https://x.com/jobs/2")
        assert a != b

    def test_differs_on_different_company(self):
        a = dedup_key("Anthropic", "SWE Intern", "https://x.com/jobs/1")
        b = dedup_key("OpenAI", "SWE Intern", "https://x.com/jobs/1")
        assert a != b

    def test_external_id_disambiguates_same_title_and_path(self):
        # Real case: Greenhouse puts the job id in the query string, which
        # normalize_url drops. Same role/title at the same path but different
        # ids (e.g. two locations) must stay distinct.
        a = dedup_key("Stripe", "SWE Intern", "https://x.com/jobs/search?gh_jid=1", "1")
        b = dedup_key("Stripe", "SWE Intern", "https://x.com/jobs/search?gh_jid=2", "2")
        assert a != b

    def test_external_id_takes_precedence_over_url(self):
        # Same id => same listing, even if the surrounding URL differs.
        a = dedup_key("Stripe", "SWE Intern", "https://x.com/a?gh_jid=1", "1")
        b = dedup_key("Stripe", "SWE Intern", "https://x.com/b?gh_jid=1", "1")
        assert a == b
