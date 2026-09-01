"""Wall-clock countdown timer with Qt signal integration."""
from datetime import datetime, timedelta
from typing import Optional
from PySide6.QtCore import QObject, QTimer, Signal
from utils.logger import get_logger

logger = get_logger(__name__)


class BlockTimer(QObject):
    """
    Precision countdown timer that emits Qt signals for UI updates.
    Uses wall-clock datetime comparisons to prevent event-loop timing drift.
    """

    tick = Signal(int)  # Emits remaining seconds
    finished = Signal()  # Emits when timer reaches 0
    started = Signal(int)  # Emits with initial duration
    stopped = Signal()  # Emits when manually stopped

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._qtimer = QTimer(self)
        self._qtimer.setInterval(1000)  # 1 second interval
        self._qtimer.timeout.connect(self._on_interval)

        self._end_time: Optional[datetime] = None
        self._total_duration: int = 0
        self._is_running: bool = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def remaining_seconds(self) -> int:
        if not self._is_running or not self._end_time:
            return 0
        diff = (self._end_time - datetime.now()).total_seconds()
        return max(0, int(diff))

    def start(self, duration_seconds: int, start_time: Optional[datetime] = None) -> None:
        """Starts countdown for given duration in seconds."""
        base_time = start_time or datetime.now()
        self._total_duration = duration_seconds
        self._end_time = base_time + timedelta(seconds=duration_seconds)
        self._is_running = True

        logger.info("Timer started for %d seconds (target: %s)", duration_seconds, self._end_time)
        self.started.emit(duration_seconds)
        self._qtimer.start()
        # Immediately emit the first tick
        self.tick.emit(self.remaining_seconds)

    def stop(self) -> None:
        """Stops the active timer."""
        if not self._is_running:
            return
        self._is_running = False
        self._qtimer.stop()
        self._end_time = None
        logger.info("Timer stopped manually.")
        self.stopped.emit()

    def _on_interval(self) -> None:
        """Internal 1-second interval handler."""
        if not self._is_running or not self._end_time:
            return

        remaining = self.remaining_seconds
        if remaining <= 0:
            self._is_running = False
            self._qtimer.stop()
            self._end_time = None
            logger.info("Timer reached zero. Emitting finished signal.")
            self.tick.emit(0)
            self.finished.emit()
        else:
            self.tick.emit(remaining)
