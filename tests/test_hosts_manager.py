"""Unit tests for HostsManager using temporary isolated files."""
import pytest
from pathlib import Path
from core.hosts_manager import HostsManager
from utils.config import BLOCK_MARKER_START, BLOCK_MARKER_END, LOOPBACK_IPV4


@pytest.fixture
def temp_hosts_env(tmp_path: Path):
    """Creates a temporary hosts file and backup path."""
    hosts_file = tmp_path / "hosts"
    backup_file = tmp_path / "hosts.backup"

    initial_content = (
        "# Copyright (c) 1993-2009 Microsoft Corp.\n"
        "127.0.0.1       localhost\n"
        "::1             localhost\n"
        "192.168.1.50    mydevserver.local\n"
    )
    hosts_file.write_text(initial_content, encoding="utf-8")

    manager = HostsManager(hosts_path=hosts_file, backup_path=backup_file)
    return manager, hosts_file, backup_file


class TestHostsManager:
    def test_backup_and_restore(self, temp_hosts_env):
        manager, hosts_file, backup_file = temp_hosts_env
        assert not backup_file.exists()

        # Perform backup
        assert manager.backup() is True
        assert backup_file.exists()
        assert backup_file.read_text(encoding="utf-8") == hosts_file.read_text(encoding="utf-8")

        # Mutate hosts file
        hosts_file.write_text("corrupted content", encoding="utf-8")

        # Restore
        assert manager.restore_backup() is True
        assert "mydevserver.local" in hosts_file.read_text(encoding="utf-8")

    def test_write_blocked_creates_markers_and_preserves_external(self, temp_hosts_env):
        manager, hosts_file, _ = temp_hosts_env

        domains = ["youtube.com", "reddit.com"]
        assert manager.write_blocked(domains) is True

        content = hosts_file.read_text(encoding="utf-8")

        # External entries must still exist
        assert "127.0.0.1       localhost" in content
        assert "192.168.1.50    mydevserver.local" in content

        # Markers must exist
        assert BLOCK_MARKER_START in content
        assert BLOCK_MARKER_END in content

        # Bare and www entries must exist
        assert f"{LOOPBACK_IPV4} youtube.com" in content
        assert f"{LOOPBACK_IPV4} www.youtube.com" in content
        assert f"{LOOPBACK_IPV4} reddit.com" in content
        assert f"{LOOPBACK_IPV4} www.reddit.com" in content

    def test_clear_blocked_removes_only_managed_section(self, temp_hosts_env):
        manager, hosts_file, _ = temp_hosts_env

        # Write then clear
        manager.write_blocked(["youtube.com"])
        assert BLOCK_MARKER_START in hosts_file.read_text(encoding="utf-8")

        assert manager.clear_blocked() is True
        cleaned_content = hosts_file.read_text(encoding="utf-8")

        # Managed markers and blocked domains should be gone
        assert BLOCK_MARKER_START not in cleaned_content
        assert BLOCK_MARKER_END not in cleaned_content
        assert "youtube.com" not in cleaned_content

        # External original lines must be untouched
        assert "127.0.0.1       localhost" in cleaned_content
        assert "mydevserver.local" in cleaned_content

    def test_skips_externally_configured_domain(self, temp_hosts_env):
        manager, hosts_file, _ = temp_hosts_env

        # Add custom external mapping
        hosts_file.write_text("10.0.0.5 custom.com\n", encoding="utf-8")

        manager.write_blocked(["custom.com", "netflix.com"])
        content = hosts_file.read_text(encoding="utf-8")

        # Should preserve the external custom.com
        assert "10.0.0.5 custom.com" in content
        # Should not duplicate custom.com with 127.0.0.1 inside managed section
        assert f"{LOOPBACK_IPV4} custom.com" not in content
        # But netflix.com should be added
        assert f"{LOOPBACK_IPV4} netflix.com" in content
