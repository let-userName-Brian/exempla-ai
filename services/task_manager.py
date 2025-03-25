import threading
import signal
import time
from typing import Dict, Set, Any
import sys

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.shutdown_event = threading.Event()
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def register_task(self, task_id: str, task: Any):
        """register a new background task"""
        with self.lock:
            self.tasks[task_id] = task
            print(f"Task {task_id} registered. Total tasks: {len(self.tasks)}")

    def unregister_task(self, task_id: str):
        """unregister a completed task"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                print(
                    f"Task {task_id} unregistered. Remaining tasks: {len(self.tasks)}"
                )

    def get_active_tasks(self) -> Set[str]:
        """get active tasks"""
        with self.lock:
            return set(self.tasks.keys())

    def handle_shutdown(self, signum, frame):
        print(f"Received shutdown signal {signum}. Initiating graceful shutdown...")
        self.shutdown_event.set()

        print(f"Waiting for {len(self.tasks)} background tasks to complete...")
        shutdown_timeout = 30  # secs

        start_time = time.time()
        while self.tasks and time.time() - start_time < shutdown_timeout:
            time.sleep(1)
            print(f"Still waiting for {len(self.tasks)} tasks...")

        if self.tasks:
            print(f"Forcing shutdown with {len(self.tasks)} tasks still running")
        else:
            print("All tasks completed successfully")

        # exit after timeout
        if signum == signal.SIGINT:
            sys.exit(130)
        else:
            sys.exit(0)

    def should_shutdown(self) -> bool:
        """Check if shutdown has been requested"""
        return self.shutdown_event.is_set()


task_manager = TaskManager()
__all__ = ["task_manager"]