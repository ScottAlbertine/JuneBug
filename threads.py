"""Data structure for storing the tracked threads under a given `Session`."""
from constants import Message
from enums import ThreadState
from models import Thread


class Threads:
    """
    Data structure for storing the tracked threads under a given `Session`.
    The way DAP handles threads is very stupid.
    You can, and should, dynamically fetch the list of all threads from DAP at any time.
    However, that list only contains ID and name, that's it.
    You have to manually track the status on your side, along with the current thread.
    That is what this data structure is for.
    """

    def __init__(self):
        self._threads: dict[int, Thread] = {}
        # Shortcut, to save on time
        self._current_thread_id: int | None = None

    def refresh(self, dap_threads_response: Message) -> list[Thread]:
        """
        Refresh our registry of tracked threads based DAP's response to a 'threads' request.
        Returns all the threads we're tracking, after the refresh, sorted by id.
        """
        # remove any thread that doesn't show up on an update.
        to_remove = set(self._threads.keys())
        for dap_thread in dap_threads_response["body"]["threads"]:
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

        if len(self._threads) == 1:
            self._current_thread_id = next(iter(self._threads.keys()))
            self._threads[self._current_thread_id].is_current = True

        return [self._threads[thread_id] for thread_id in sorted(self._threads.keys())]

    def update(self, dap_thread_event: Message) -> None:
        """Update a single thread based on a 'thread' event from DAP."""
        body = dap_thread_event["body"]
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

    def pause_at_start(self) -> None:
        """
        For sessions we own, we expect all threads to be paused at startup, even though DAP doesn't tell us this.
        Should only ever be called once per session.
        """
        for thread in self._threads.values():
            thread.state = ThreadState.PAUSED

    def set_current(self, thread_id: int) -> None:
        """Set the thread with the given ID as the current thread, all others as not the current thread."""
        self._current_thread_id = thread_id
        for thread in self._threads.values():
            thread.is_current = (thread.id == thread_id)

    def get_current_thread_id(self) -> int | None:
        return self._current_thread_id
