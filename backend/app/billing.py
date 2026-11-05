"""Extension point for usage accounting and subscription limits.

Self-use builds allow every request. A later billing module can replace these
two methods without touching the queue or the inference pipeline.
"""

import logging

logger = logging.getLogger(__name__)


class UsageLedger:
    def authorize(self, username: str) -> None:
        """Reject here when a subscription quota is exceeded."""
        return

    def record(self, username: str, task_id: str, duration_sec: float, status: str) -> None:
        """Persist usage once a task finishes. Currently a log line only."""
        logger.info(
            "usage user=%s task=%s seconds=%.3f status=%s",
            username,
            task_id,
            duration_sec,
            status,
        )


ledger = UsageLedger()
