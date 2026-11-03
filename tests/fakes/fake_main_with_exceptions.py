"""Fake main module, with exceptions, for testing."""

from tests.fakes.fake_exceptions import SomeCaughtException, SomeUnCaughtException


def main() -> None:
    try:
        print("it got into the try", flush=True)
        raise SomeCaughtException("arg1", "arg2")
    except SomeCaughtException:
        print("it got into the except", flush=True)
    finally:
        print("it got into the finally", flush=True)

    print("it left the try block", flush=True)

    raise SomeUnCaughtException("arg1", "arg2")


if __name__ == "__main__":
    main()
