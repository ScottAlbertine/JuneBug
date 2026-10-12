"""Fake multi-threaded module, for testing thread listing."""
import threading
from time import sleep


def worker_done() -> None:
    """Do nothing, immediately exit."""
    pass


def worker_busy() -> None:
    """Thread that loops forever doing busy work."""
    while True:
        pass


def worker_daemon() -> None:
    """Daemon thread that sleeps forever."""
    while True:
        sleep(1)


def main() -> None:
    print("multi-thread process started")

    threads = [
        threading.Thread(target=worker_busy, name="BusyWorker"),
        threading.Thread(target=worker_done, name="DoneWorker"),
        threading.Thread(target=worker_daemon, name="DaemonOne", daemon=True),
        threading.Thread(target=worker_daemon, name="DaemonTwo", daemon=True),
    ]

    for t in threads:
        t.start()

    while True:
        sleep(1)


if __name__ == "__main__":
    main()
