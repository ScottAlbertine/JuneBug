"""Fake main module, with an import, for testing."""

from tests.fakes.fake_library import add

module_scoped_string = "out here"

def main() -> None:
    print("it started", flush=True)

    function_scoped_string = "in here"

    five = add(2, 3)
    print("it finished", flush=True)


if __name__ == "__main__":
    main()
