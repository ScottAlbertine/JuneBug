import threading
from time import sleep

def worker():
    print("Worker started", flush=True)
    while True:
        print("Working", flush=True)
        sleep(1)

if __name__ == '__main__':
    print("Main started", flush=True)
    threading.Thread(target=worker, daemon=False).start()

    # main() returns here — main thread is DONE
    # Process stays alive until worker finishes

print("This is the last line of main.py, and it has been run", flush=True)