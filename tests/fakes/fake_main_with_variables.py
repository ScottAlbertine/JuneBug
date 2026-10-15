from enum import Enum


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class Window:
    def __init__(self) -> None:
        self.state = "down"


class Door:
    def __init__(self):
        self.window = Window()


class Car:
    def __init__(self):
        self.color = Color.RED
        self.name = "Greased Lightning"
        self.doors = [Door(), Door(), Door(), Door()]


def main() -> None:
    some_string = "some string"
    some_int = 123
    some_float = 1.23
    some_bool = True
    some_list = [1, 2, 3]
    some_tuple = (1, 2, 3)
    some_dict = {"a": 1, "b": 2, "c": 3}
    some_object = Car()
    some_enum = Color.RED

    some_breakpoint = "now"  # we don't expect to see this in our variables


if __name__ == "__main__":
    main()
