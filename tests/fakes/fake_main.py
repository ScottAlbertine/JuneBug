"""Fake main module, for testing."""
import sys
from time import sleep


def main(args: list[str]) -> None:
    print("it started")
    if "--loop-forever" in args:
        while True:
            sleep(1)
            print("it looped")

    print("it finished")


if __name__ == "__main__":
    main(sys.argv)
