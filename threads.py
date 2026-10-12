"""Data structure for storing the tracked threads under a given `Session`."""

from dap import Event

from enums import ThreadState
from models import Thread


class Threads:
    """Data structure for storing the tracked threads under a given `Session`."""

    def __init__(self):
        self._threads: dict[int, Thread] = {}

    def refresh(self, dap_threads: Event) -> list[Thread]:
        """
        Refresh our registry of tracked threads based DAP's response to a 'threads' request.
        Returns all the threads we're tracking, after the refresh, sorted by id.
        """
        # remove any thread that doesn't show up on an update.
        to_remove = set(self._threads.keys())
        for dap_thread in dap_threads.body["body"]["threads"]:
            thread_id: int = dap_thread["id"]
            thread_name: str = dap_thread["name"]
            if thread_id in self._threads:
                self._threads[thread_id].name = thread_name
                to_remove.remove(thread_id)  # keep it
            else:
                self._threads[thread_id] = Thread(
                    id=thread_id, name=thread_name, state=ThreadState.UNKNOWN, is_current=False,
                )

        for thread_id in to_remove:
            del self._threads[thread_id]

        return [self._threads[id] for id in sorted(self._threads.keys())]

    def update(self, dap_thread_event: Event) -> None:
        """Update a single thread based on a 'thread' event from DAP."""
        body = dap_thread_event.body
        thread_id = body["threadId"]
        reason = body.get("reason")
        if reason == "exited":
            self._threads.pop(thread_id, None)
            return

        if thread_id not in self._threads:
            self._threads[thread_id] = Thread(
                id=thread_id, name=None, state=ThreadState.UNKNOWN, is_current=False,
            )
        if reason == "started":
            self._threads[thread_id].state = ThreadState.RUNNING
        if reason == "pause":
            self._threads[thread_id].state = ThreadState.PAUSED
        if body.get("allThreadsStopped"):
            for thread in self._threads.values():
                thread.state = ThreadState.PAUSED
        if body.get("allThreadsContinued"):
            for thread in self._threads.values():
                thread.state = ThreadState.RUNNING
