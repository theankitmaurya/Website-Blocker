"""Unit tests for BlockerService."""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock
from database.database import DatabaseManager
from core.hosts_manager import HostsManager
from core.blocker import BlockerService, BlockerError


@pytest.fixture
def test_setup(tmp_path: Path):
    db_file = tmp_path / "test_blocker.db"
    db = DatabaseManager(db_path=db_file)
    db.initialize()

    mock_hosts = MagicMock(spec=HostsManager)
    mock_hosts.write_blocked.return_value = True
    mock_hosts.clear_blocked.return_value = True
    mock_hosts.flush_dns.return_value = True

    blocker = BlockerService(db=db, hosts_manager=mock_hosts)
    return db, mock_hosts, blocker


class TestBlockerService:
    def test_start_session_success(self, test_setup):
        db, mock_hosts, blocker = test_setup

        session = blocker.start_session(domains=["youtube.com", "reddit.com"], duration_seconds=3600)
        assert session.id is not None
        assert session.duration_seconds == 3600
        assert session.status == "active"

        mock_hosts.write_blocked.assert_called_once_with(["youtube.com", "reddit.com"])
        mock_hosts.flush_dns.assert_called_once()

        # Database active session exists
        active = db.get_active_session()
        assert active is not None
        assert active.id == session.id

    def test_start_session_empty_domains_raises(self, test_setup):
        _, mock_hosts, blocker = test_setup
        with pytest.raises(BlockerError):
            blocker.start_session(domains=[], duration_seconds=1800)

    def test_end_session(self, test_setup):
        db, mock_hosts, blocker = test_setup

        session = blocker.start_session(domains=["youtube.com"], duration_seconds=3600)
        assert session.id is not None

        assert blocker.end_session(session.id, status="completed") is True
        mock_hosts.clear_blocked.assert_called_once()

        # Session in DB should now be completed
        assert db.get_active_session() is None
        sessions = db.get_sessions()
        assert len(sessions) == 1
        assert sessions[0].status == "completed"

    def test_recover_expired_session(self, test_setup):
        db, mock_hosts, blocker = test_setup

        # Insert expired session (started 2 hours ago for 1 hour duration)
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        db.create_session(duration_seconds=3600, start_time=old_time)

        recovered = blocker.recover_interrupted_session()
        # Should clean up and return None
        assert recovered is None
        mock_hosts.clear_blocked.assert_called_once()
        assert db.get_active_session() is None

    def test_recover_active_ongoing_session(self, test_setup):
        db, mock_hosts, blocker = test_setup

        db.add_website("youtube.com", enabled=True)

        # Insert ongoing session (started 10 mins ago for 1 hour duration)
        recent_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        db.create_session(duration_seconds=3600, start_time=recent_time)

        recovered = blocker.recover_interrupted_session()
        assert recovered is not None
        assert recovered.duration_seconds == 3600
        mock_hosts.write_blocked.assert_called_once_with(["youtube.com"])
