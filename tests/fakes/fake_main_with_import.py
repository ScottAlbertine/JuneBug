"""Fake main module, with an import, for testing."""

from tests.fakes.fake_library import add


def main() -> None:
    print("it started", flush=True)

    five = add(2, 3)
    print("it finished", flush=True)


if __name__ == "__main__":
    main()
