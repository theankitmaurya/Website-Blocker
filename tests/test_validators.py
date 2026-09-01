"""Unit tests for domain normalization and validation utilities."""
import pytest
from utils.validators import normalize_domain, is_valid_domain


class TestValidators:
    @pytest.mark.parametrize(
        "raw_input,expected",
        [
            ("youtube.com", "youtube.com"),
            ("www.youtube.com", "youtube.com"),
            ("https://www.youtube.com/watch?v=123", "youtube.com"),
            ("http://reddit.com/r/python", "reddit.com"),
            ("HTTPS://INSTAGRAM.COM/p/abc", "instagram.com"),
            ("facebook.com/", "facebook.com"),
            ("www.netflix.com:443", "netflix.com"),
            ("sub.domain.co.uk", "sub.domain.co.uk"),
            ("x.com", "x.com"),
            ("192.168.1.1", "192.168.1.1"),
        ],
    )
    def test_normalize_domain_valid(self, raw_input: str, expected: str):
        assert normalize_domain(raw_input) == expected

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "",
            "   ",
            "hello",
            "hello world",
            "http://",
            "https://",
            "random text with spaces",
            "http:///example.com",
            "-youtube.com",
            "youtube-.com",
            "youtube..com",
        ],
    )
    def test_normalize_domain_invalid(self, invalid_input: str):
        assert normalize_domain(invalid_input) is None

    @pytest.mark.parametrize(
        "domain,expected",
        [
            ("youtube.com", True),
            ("reddit.com", True),
            ("sub.example.org", True),
            ("a.b.c.d.e.com", True),
            ("127.0.0.1", True),
            ("10.0.0.1", True),
            ("hello", False),
            ("", False),
            (" ", False),
            ("-test.com", False),
            ("test-.com", False),
            ("test..com", False),
            ("256.256.256.256", False),
        ],
    )
    def test_is_valid_domain(self, domain: str, expected: bool):
        assert is_valid_domain(domain) is expected

    @pytest.mark.parametrize(
        "raw_input,expected_name",
        [
            ("youtube.com", "YouTube"),
            ("https://www.youtube.com/watch?v=123", "YouTube"),
            ("reddit.com", "Reddit"),
            ("https://instagram.com/p/abc", "Instagram"),
            ("netflix.com", "Netflix"),
            ("twitter.com", "Twitter"),
            ("x.com", "X (Twitter)"),
            ("news.ycombinator.com", "Hacker News"),
            ("chatgpt.com", "ChatGPT"),
            ("sub.example.co.uk", "Example"),
            ("my-productivity-hub.org", "My Productivity Hub"),
            ("192.168.1.1", "192.168.1.1"),
            ("", ""),
        ],
    )
    def test_get_website_name(self, raw_input: str, expected_name: str):
        from utils.validators import get_website_name
        assert get_website_name(raw_input) == expected_name

