"""Blocker service orchestrating hosts modification, DNS flushing, and session state."""
from datetime import datetime, timedelta
from typing import List, Optional
from core.hosts_manager import HostsManager, HostsManagerError
from database.database import DatabaseManager
from database.models import Session
from utils.logger import get_logger

logger = get_logger(__name__)


class BlockerError(Exception):
    """Raised when blocking operation fails."""
    pass


class BlockerService:
    """Orchestrates blocking sessions, hosts file updates, and persistence."""

    def __init__(self, db: DatabaseManager, hosts_manager: HostsManager):
        self.db = db
        self.hosts = hosts_manager

    def start_session(
        self,
        domains: List[str],
        duration_seconds: int,
        session_type: str = "manual",
    ) -> Session:
        """
        Starts a new blocking session:
        1. Validates domain list.
        2. Writes block entries to hosts file.
        3. Flushes DNS cache.
        4. Creates active session record in database.
        """
        if not domains:
            raise BlockerError("No websites selected for blocking.")

        logger.info("Starting blocking session for %d domains (duration: %d seconds)", len(domains), duration_seconds)

        # 1. Update hosts file
        try:
            self.hosts.write_blocked(domains)
        except HostsManagerError as e:
            logger.error("Failed to write to hosts file: %s", e)
            raise BlockerError(f"Failed to modify hosts file: {e}") from e

        # 2. Flush DNS
        self.hosts.flush_dns()

        # 3. Create active session in database
        session = self.db.create_session(
            duration_seconds=duration_seconds,
            session_type=session_type,
            status="active",
        )
        return session

    def end_session(self, session_id: int, status: str = "completed") -> bool:
        """
        Ends an active blocking session:
        1. Clears application-managed block entries from hosts file.
        2. Flushes DNS cache.
        3. Updates session status in database.
        """
        logger.info("Ending session #%d with status '%s'", session_id, status)

        # 1. Clear hosts file
        try:
            self.hosts.clear_blocked()
        except HostsManagerError as e:
            logger.error("Failed to clear hosts file: %s", e)

        # 2. Flush DNS
        self.hosts.flush_dns()

        # 3. Mark session in database
        return self.db.end_session(session_id, status=status)

    def recover_interrupted_session(self) -> Optional[Session]:
        """
        Startup check for interrupted or ongoing sessions:
        - If an active session exists and its duration has expired, cleanly ends it.
        - If an active session exists and has remaining time, ensures hosts file is blocked and returns the session.
        - If no active session exists, ensures hosts file has no leftover blocked entries.
        """
        active_session = self.db.get_active_session()
        if not active_session:
            # Ensure hosts file is clean if no active session
            try:
                self.hosts.clear_blocked()
            except Exception as e:
                logger.warning("Could not verify/clean hosts file on startup: %s", e)
            return None

        try:
            start_dt = datetime.fromisoformat(active_session.start_time)
            end_expected = start_dt + timedelta(seconds=active_session.duration_seconds)
            now = datetime.now()

            if now >= end_expected:
                logger.info(
                    "Found expired active session #%d from previous run. Cleaning up.",
                    active_session.id,
                )
                self.end_session(active_session.id or 0, status="completed")
                return None
            else:
                remaining_sec = int((end_expected - now).total_seconds())
                logger.info(
                    "Resuming active session #%d with %d seconds remaining.",
                    active_session.id,
                    remaining_sec,
                )
                # Re-apply enabled websites to hosts file in case machine was restarted
                enabled_domains = [w.domain for w in self.db.get_websites() if w.enabled]
                if enabled_domains:
                    self.hosts.write_blocked(enabled_domains)
                    self.hosts.flush_dns()
                return active_session
        except Exception as e:
            logger.error("Error during session recovery: %s", e)
            if active_session and active_session.id:
                self.end_session(active_session.id, status="interrupted")
            return None
