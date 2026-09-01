"""Unit tests for BlockTimer."""
import pytest
from datetime import datetime, timedelta
from PySide6.QtCore import QCoreApplication
from core.timer import BlockTimer

# Ensure a QCoreApplication instance exists for signal/timer testing
app = QCoreApplication.instance() or QCoreApplication([])


class TestBlockTimer:
    def test_timer_initial_state(self):
        timer = BlockTimer()
        assert timer.is_running is False
        assert timer.remaining_seconds == 0

    def test_timer_start_and_remaining(self):
        timer = BlockTimer()
        ticks = []
        timer.tick.connect(lambda s: ticks.append(s))

        timer.start(duration_seconds=60)
        assert timer.is_running is True
        assert 58 <= timer.remaining_seconds <= 60
        assert len(ticks) >= 1
        assert 58 <= ticks[0] <= 60

        timer.stop()
        assert timer.is_running is False
        assert timer.remaining_seconds == 0

    def test_timer_wall_clock_expiry(self):
        timer = BlockTimer()
        finished_called = []
        timer.finished.connect(lambda: finished_called.append(True))

        # Start with a past start_time
        past_start = datetime.now() - timedelta(seconds=100)
        timer.start(duration_seconds=10, start_time=past_start)

        # Trigger interval
        timer._on_interval()
        assert len(finished_called) == 1
        assert timer.is_running is False
