"""Domain manager service bridging UI with Database operations."""
from typing import List, NamedTuple, Optional
from database.database import DatabaseManager
from database.models import Website
from utils.validators import normalize_domain, is_valid_domain
from utils.logger import get_logger

logger = get_logger(__name__)


class AddResult(NamedTuple):
    success: bool
    domain: Optional[str]
    error: Optional[str]  # "invalid" | "duplicate" | None


class DomainManager:
    """Handles domain validation, normalization, and persistence."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def add(self, raw_input: str) -> AddResult:
        """
        Normalizes and adds a domain to the blocklist.
        Returns AddResult with success flag and error detail if failed.
        """
        normalized = normalize_domain(raw_input)
        if not normalized or not is_valid_domain(normalized):
            return AddResult(success=False, domain=None, error="invalid")

        # Check if already exists in database
        existing = self.db.get_website_by_domain(normalized)
        if existing:
            return AddResult(success=False, domain=normalized, error="duplicate")

        # Persist to database
        self.db.add_website(domain=normalized, enabled=True)
        return AddResult(success=True, domain=normalized, error=None)

    def remove(self, website_id: int) -> bool:
        """Removes a website by ID."""
        return self.db.remove_website(website_id)

    def toggle(self, website_id: int, enabled: bool) -> bool:
        """Toggles enabled state of a website."""
        return self.db.toggle_website(website_id, enabled)

    def list_all(self) -> List[Website]:
        """Lists all configured websites."""
        return self.db.get_websites()

    def get_enabled_domains(self) -> List[str]:
        """Returns list of bare domain strings that are enabled for blocking."""
        websites = self.db.get_websites()
        return [w.domain for w in websites if w.enabled]
