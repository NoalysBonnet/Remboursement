import os
import time

class FileLock:
    def __init__(self, lock_file_path, timeout=10):
        self.lock_file_path = lock_file_path
        self.timeout = timeout
        self._lock_file_handle = None

    def acquire(self):
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                self._lock_file_handle = os.open(self.lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return
            except FileExistsError:
                time.sleep(0.1)
        raise TimeoutError(f"Impossible d'acquérir le verrou sur {self.lock_file_path} après {self.timeout} secondes.")

    def release(self):
        if self._lock_file_handle is not None:
            os.close(self._lock_file_handle)
            self._lock_file_handle = None
        try:
            os.remove(self.lock_file_path)
        except FileNotFoundError:
            pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()