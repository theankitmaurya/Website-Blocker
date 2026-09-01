"""Windows Hosts file manager for safe website blocking."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Set, Tuple
from utils.config import (
    BLOCK_MARKER_START,
    BLOCK_MARKER_END,
    DEFAULT_HOSTS_PATH,
    DEFAULT_HOSTS_BACKUP_PATH,
    LOOPBACK_IPV4,
    LOOPBACK_IPV6,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class HostsManagerError(Exception):
    """Raised when hosts file operations fail."""
    pass


class HostsManager:
    """Safely manages block entries inside the Windows hosts file."""

    def __init__(
        self,
        hosts_path: Optional[Path] = None,
        backup_path: Optional[Path] = None,
    ):
        self.hosts_path = Path(hosts_path or DEFAULT_HOSTS_PATH)
        self.backup_path = Path(backup_path or DEFAULT_HOSTS_BACKUP_PATH)

    def backup(self) -> bool:
        """
        Creates or updates a backup copy of the current hosts file.
        Returns True on success, False otherwise.
        """
        try:
            if not self.hosts_path.exists():
                logger.warning("Hosts file not found at %s. Creating empty file.", self.hosts_path)
                self.hosts_path.parent.mkdir(parents=True, exist_ok=True)
                self.hosts_path.write_text("", encoding="utf-8")

            shutil.copy2(str(self.hosts_path), str(self.backup_path))
            logger.info("Created hosts file backup at %s", self.backup_path)
            return True
        except Exception as e:
            logger.error("Failed to backup hosts file: %s", e)
            return False

    def restore_backup(self) -> bool:
        """
        Restores the hosts file from its backup copy.
        Returns True on success, False otherwise.
        """
        try:
            if not self.backup_path.exists():
                logger.error("Backup file %s does not exist.", self.backup_path)
                return False

            shutil.copy2(str(self.backup_path), str(self.hosts_path))
            logger.info("Restored hosts file from %s", self.backup_path)
            return True
        except Exception as e:
            logger.error("Failed to restore hosts file from backup: %s", e)
            return False

    def read_raw(self) -> str:
        """Reads and returns the raw contents of the hosts file."""
        if not self.hosts_path.exists():
            return ""
        try:
            return self.hosts_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error("Failed to read hosts file: %s", e)
            raise HostsManagerError(f"Could not read hosts file: {e}") from e

    def _split_sections(self, content: str) -> Tuple[List[str], List[str], List[str]]:
        """
        Splits hosts file content into (pre_lines, managed_lines, post_lines).
        - pre_lines: lines before BLOCK_MARKER_START
        - managed_lines: lines between markers (managed by this app)
        - post_lines: lines after BLOCK_MARKER_END
        """
        lines = content.splitlines()
        pre_lines: List[str] = []
        managed_lines: List[str] = []
        post_lines: List[str] = []

        in_managed = False
        after_managed = False

        for line in lines:
            stripped = line.strip()
            if stripped == BLOCK_MARKER_START:
                in_managed = True
                continue
            elif stripped == BLOCK_MARKER_END:
                in_managed = False
                after_managed = True
                continue

            if in_managed:
                managed_lines.append(line)
            elif after_managed:
                post_lines.append(line)
            else:
                pre_lines.append(line)

        return pre_lines, managed_lines, post_lines

    def get_external_domains(self) -> Set[str]:
        """
        Parses and returns all domains defined outside of application markers.
        """
        raw = self.read_raw()
        pre, _, post = self._split_sections(raw)
        external_domains: Set[str] = set()

        for line in pre + post:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split()
            if len(parts) >= 2:
                # parts[0] is IP, parts[1:] are hostnames/domains
                for host in parts[1:]:
                    external_domains.add(host.lower().strip())

        return external_domains

    def _atomic_write(self, content: str) -> None:
        """
        Writes content to hosts file atomically using a temporary file and replace.
        """
        target_dir = self.hosts_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        temp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=str(target_dir),
                delete=False,
                encoding="utf-8",
                newline="\n",
            ) as f:
                temp_file = Path(f.name)
                f.write(content)
                if not content.endswith("\n"):
                    f.write("\n")

            # Atomically replace destination
            os.replace(str(temp_file), str(self.hosts_path))
        except Exception as e:
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            logger.error("Failed to write to hosts file: %s", e)
            raise HostsManagerError(f"Permission denied or error writing to hosts file: {e}") from e

    def write_blocked(self, domains: List[str]) -> bool:
        """
        Safely writes block entries for given domains inside application markers.
        Creates backup prior to modification.
        """
        if not domains:
            return self.clear_blocked()

        self.backup()

        raw = self.read_raw()
        pre, _, post = self._split_sections(raw)
        external_domains = self.get_external_domains()

        # Build managed block entries
        block_lines: List[str] = []
        block_lines.append(BLOCK_MARKER_START)
        block_lines.append(f"# Added automatically by Website Blocker at {Path(self.hosts_path).name}")

        added_hosts: Set[str] = set()
        for domain in domains:
            clean = domain.strip().lower()
            if not clean:
                continue

            # Bare and www variants
            variants = [clean]
            if not clean.startswith("www."):
                variants.append(f"www.{clean}")

            for host in variants:
                if host in added_hosts:
                    continue
                if host in external_domains:
                    logger.warning("Skipping '%s' as it is already configured in external hosts lines.", host)
                    continue

                added_hosts.add(host)
                block_lines.append(f"{LOOPBACK_IPV4} {host}")
                block_lines.append(f"{LOOPBACK_IPV6} {host}")

        block_lines.append(BLOCK_MARKER_END)

        # Assemble new file content
        new_lines = []
        if pre:
            new_lines.extend(pre)
            # Ensure a clean blank line separator before markers
            if pre[-1].strip():
                new_lines.append("")

        new_lines.extend(block_lines)

        if post:
            if post[0].strip():
                new_lines.append("")
            new_lines.extend(post)

        assembled = "\n".join(new_lines) + "\n"
        self._atomic_write(assembled)
        logger.info("Successfully updated hosts file with %d blocked domain variants.", len(added_hosts))
        return True

    def clear_blocked(self) -> bool:
        """
        Removes only the application-managed block section from the hosts file.
        Leaves all external entries intact.
        """
        self.backup()
        raw = self.read_raw()
        pre, managed, post = self._split_sections(raw)

        if not managed:
            # Nothing to clean
            return True

        # Assemble cleaned content
        new_lines = []
        if pre:
            new_lines.extend(pre)
        if post:
            # Avoid excessive blank lines
            if pre and pre[-1].strip() and post[0].strip():
                new_lines.append("")
            new_lines.extend(post)

        assembled = "\n".join(new_lines).strip()
        if assembled:
            assembled += "\n"

        self._atomic_write(assembled)
        logger.info("Successfully cleared application-managed entries from hosts file.")
        return True

    def flush_dns(self) -> bool:
        """
        Executes Windows DNS cache flush via 'ipconfig /flushdns'.
        """
        try:
            res = subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if res.returncode == 0:
                logger.info("DNS cache flushed successfully.")
                return True
            else:
                logger.warning("DNS cache flush returned code %d: %s", res.returncode, res.stderr)
                return False
        except Exception as e:
            logger.warning("Failed to execute DNS cache flush: %s", e)
            return False
