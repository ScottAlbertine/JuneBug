from typing import Annotated

ProjectPath = Annotated[
    str | None,
    "The project path. Pass this value ALWAYS if you are aware of it. It reduces numbers of ambiguous calls. \n "
    "In the case you know only the current working directory you can use it as the project path.\n "
    "If you're not aware about the project path you can ask user about it."
]
