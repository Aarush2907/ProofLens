from app.research.quality import assess_source, domain_of


def test_domain_drops_www_and_port():
    assert domain_of("https://www.nature.com/article") == "nature.com"
    assert domain_of("https://cdc.gov:443/sleep") == "cdc.gov"


def test_primary_style_requires_an_academic_host_and_original_data_language():
    assessment = assess_source(
        {
            "url": "https://www.cdc.gov/sleep",
            "domain": "cdc.gov",
            "title": "Sleep trial",
            "author": "Centers for Disease Control",
            "published_on": "2024-03-02",
            "content": "We measured recall in 40 adults. Our results are in the table.",
            "snippet": "",
        }
    )
    assert assessment["role"] == "primary"
    assert assessment["author_known"] is True
    assert assessment["date_known"] is True
    assert "score" not in assessment
    assert any("separate from whether a particular claim is verified" in reason for reason in assessment["reasons"])


def test_news_domain_without_original_data_is_secondary():
    assessment = assess_source(
        {
            "url": "https://www.reuters.com/sleep",
            "domain": "reuters.com",
            "title": "Sleep story",
            "author": "",
            "published_on": "",
            "content": "A study found a difference in recall.",
            "snippet": "",
        }
    )
    assert assessment["role"] == "secondary"
    assert assessment["author_known"] is False
    assert any("No publication date" in reason for reason in assessment["reasons"])


def test_one_primary_signal_stays_unclear():
    assessment = assess_source(
        {
            "url": "https://example.edu/sleep",
            "domain": "example.edu",
            "author": "",
            "published_on": "",
            "content": "Adults who slept seven hours recalled 20 percent more word pairs.",
            "snippet": "",
        }
    )
    assert assessment["role"] == "unclear"
