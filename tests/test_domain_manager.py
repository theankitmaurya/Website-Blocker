"""Unit tests for DomainManager service."""
import pytest
from pathlib import Path
from database.database import DatabaseManager
from core.domain_manager import DomainManager


@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_blocker.db"
    db = DatabaseManager(db_path=db_file)
    db.initialize()
    return db


@pytest.fixture
def domain_manager(temp_db):
    return DomainManager(temp_db)


class TestDomainManager:
    def test_add_valid_domain(self, domain_manager):
        result = domain_manager.add("youtube.com")
        assert result.success is True
        assert result.domain == "youtube.com"
        assert result.error is None

        websites = domain_manager.list_all()
        assert len(websites) == 1
        assert websites[0].domain == "youtube.com"
        assert websites[0].enabled is True

    def test_add_url_normalizes(self, domain_manager):
        result = domain_manager.add("https://www.reddit.com/r/python")
        assert result.success is True
        assert result.domain == "reddit.com"

    def test_add_invalid_domain(self, domain_manager):
        result = domain_manager.add("hello world")
        assert result.success is False
        assert result.domain is None
        assert result.error == "invalid"
        assert len(domain_manager.list_all()) == 0

    def test_add_duplicate_domain(self, domain_manager):
        res1 = domain_manager.add("instagram.com")
        assert res1.success is True

        res2 = domain_manager.add("https://www.instagram.com/explore")
        assert res2.success is False
        assert res2.domain == "instagram.com"
        assert res2.error == "duplicate"
        assert len(domain_manager.list_all()) == 1

    def test_remove_domain(self, domain_manager):
        res = domain_manager.add("twitter.com")
        websites = domain_manager.list_all()
        site_id = websites[0].id
        assert site_id is not None

        assert domain_manager.remove(site_id) is True
        assert len(domain_manager.list_all()) == 0

    def test_toggle_domain(self, domain_manager):
        domain_manager.add("netflix.com")
        site = domain_manager.list_all()[0]
        assert site.id is not None
        assert site.enabled is True

        assert domain_manager.toggle(site.id, False) is True
        assert domain_manager.list_all()[0].enabled is False
        assert domain_manager.get_enabled_domains() == []

        assert domain_manager.toggle(site.id, True) is True
        assert domain_manager.get_enabled_domains() == ["netflix.com"]
