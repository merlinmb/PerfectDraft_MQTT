import threading
from collections import deque
from datetime import datetime, timezone


class AppState:
    """Thread-safe in-memory state shared between the polling loop and the
    admin web UI: auth status plus a rolling log of recent API calls."""

    def __init__(self, max_calls=50):
        self._lock = threading.Lock()
        self._calls = deque(maxlen=max_calls)
        self.authenticated = False
        self.last_auth_time = None
        self.last_auth_error = None
        self.last_poll_time = None
        self.last_poll_error = None
        self.machine_id = None
        self.machine_info = None

    def set_auth_status(self, authenticated, error=None):
        with self._lock:
            self.authenticated = authenticated
            self.last_auth_error = error
            if authenticated:
                self.last_auth_time = datetime.now(timezone.utc).isoformat()

    def set_poll_status(self, error=None):
        with self._lock:
            self.last_poll_time = datetime.now(timezone.utc).isoformat()
            self.last_poll_error = error

    def set_machine_id(self, machine_id):
        with self._lock:
            self.machine_id = machine_id

    def set_machine_info(self, machine_info):
        with self._lock:
            self.machine_info = machine_info

    def record_call(self, method, url, status_code, response_body):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "url": url,
            "status_code": status_code,
            "response_body": response_body,
        }
        with self._lock:
            self._calls.appendleft(entry)

    def snapshot(self):
        with self._lock:
            return {
                "authenticated": self.authenticated,
                "last_auth_time": self.last_auth_time,
                "last_auth_error": self.last_auth_error,
                "last_poll_time": self.last_poll_time,
                "last_poll_error": self.last_poll_error,
                "machine_id": self.machine_id,
                "machine_info": self.machine_info,
                "calls": list(self._calls),
            }


state = AppState()
