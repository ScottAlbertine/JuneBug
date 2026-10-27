from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from tests.constants import FAKE_MAIN, FAKE_MAIN_WITH_IMPORT, FAKE_MAIN_WITH_VARIABLES
from tests.utils import MatchAny, MatchRegex, create_session, move_to_next_breakpoint


async def common_setup(client: Client) -> str:
    """
    A bunch of tests in this file use intentionally identical setup, and are read-only, so they don't alter the setup at all.
    This runs the setup once per test running session, rather than duplicating all that setup repeatedly.
    This is for test speed.
    This function returns the ID of an existing session that is stopped at a breakpoint that has a ton of variables available to it.
    """
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_VARIABLES))["id"]
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_VARIABLES, "line": 38},
    )
    await move_to_next_breakpoint(client, session_id)
    return session_id


async def test_evaluate_expression__invalid(client: Client) -> None:
    session_id = await common_setup(client)
    with pytest.raises(ToolError, match=r"Stack frame 999999 was not found\."):
        await client.call_tool(
            "evaluate_expression", {"expression": "some_list", "session_id": session_id, "frame_id": 999999},
        )

    with pytest.raises(
        ToolError, match=r"depth\n.+Input should be greater than or equal to 0.+",
    ):
        await client.call_tool(
            "evaluate_expression", {"expression": "some_list", "session_id": session_id, "depth": -1},
        )

    with pytest.raises(
        ToolError, match=r"depth\n.+Input should be less than or equal to 4.+",
    ):
        await client.call_tool(
            "evaluate_expression", {"expression": "some_list", "session_id": session_id, "depth": 5},
        )

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0"):
        await client.call_tool(
            "evaluate_expression", {"expression": "some_list", "session_id": session_id, "timeout": -1},
        )


async def test_evaluate_expression__not_top_frame(client: Client) -> None:
    """Test that we can specify a frame that's not the top of the stack, and evaluate expressions on it."""
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_IMPORT))["id"]

    # Set a breakpoint inside the add() function in fake_library (line 2: return a + b)
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": "tests/fakes/fake_library.py", "line": 2},
    )

    # Resume and wait for pause at the breakpoint
    await move_to_next_breakpoint(client, session_id)

    # Get the stack
    stack = await client.call_tool("get_stack", {"session_id": session_id})

    # Pick the second frame ID
    frame_id = stack.structured_content["frames"][1]["id"]

    # Evaluate a function scoped variable
    variable = await client.call_tool(
        "evaluate_expression", {"expression": "function_scoped_string", "session_id": session_id, "frame_id": frame_id},
    )
    assert variable.structured_content == {
        "name": "function_scoped_string",
        "value": "'in here'",
        "type": "str",
        "evaluate_name": "function_scoped_string",
        "presentation_hint": {"attributes": ["rawString"]},
        "children": None,
    }

    # Pick the first frame ID
    frame_id = stack.structured_content["frames"][0]["id"]

    # Evaluate a function scoped variable
    variable = await client.call_tool(
        "evaluate_expression", {"expression": "b", "session_id": session_id, "frame_id": frame_id},
    )
    assert variable.structured_content == {
        "name": "b", "value": "3", "type": "int", "evaluate_name": "b", "children": None,
    }


async def test_evaluate_expression__not_paused(client: Client) -> None:
    """Test that you get an appropriate error if you try to list variables when you're not paused"""
    session_id = (await create_session(client, file_path=FAKE_MAIN, program_arguments=["--loop-forever"]))["id"]

    await client.call_tool("control_debugger_session", {"session_id": session_id, "action": "resume"})

    with pytest.raises(ToolError, match=r"Session must be paused to call that tool. Session is currently running."):
        await client.call_tool("evaluate_expression", {"expression": "'works'", "session_id": session_id})


async def test_evaluate_expression__can_write(client: Client) -> None:
    """Test that evaluate_expression can edit existing data in a live python process."""

    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_VARIABLES))["id"]

    await client.call_tool(
        "run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_VARIABLES, "line": 38},
    )

    append_result = await client.call_tool(
        "evaluate_expression", {"expression": "some_list.append(4)", "session_id": session_id},
    )

    assert append_result.structured_content == {
        "name": "some_list.append(4)",
        "value": "None",
        "type": "NoneType",
        "evaluate_name": "some_list.append(4)",
        "children": None,
    }

    updated_list = await client.call_tool(
        "evaluate_expression", {"expression": "some_list", "session_id": session_id, "depth": 1},
    )
    assert updated_list.structured_content == {
        "name": "some_list",
        "value": "[1, 2, 3, 4]",
        "type": "list",
        "evaluate_name": "some_list",
        "children": [
            {"name": "0", "value": "1", "type": "int", "evaluate_name": "some_list[0]", "children": None},
            {"name": "1", "value": "2", "type": "int", "evaluate_name": "some_list[1]", "children": None},
            {"name": "2", "value": "3", "type": "int", "evaluate_name": "some_list[2]", "children": None},
            {"name": "3", "value": "4", "type": "int", "evaluate_name": "some_list[3]", "children": None},
            {
                "name": "len()",
                "value": "4",
                "type": "int",
                "evaluate_name": "len(some_list)",
                "presentation_hint": {"attributes": ["readOnly"]},
                "children": None,
            },
        ],
    }


async def test_evaluate_expression__shallow(client: Client) -> None:
    session_id = await common_setup(client)
    shallow = await client.call_tool("evaluate_expression", {"expression": "some_list", "session_id": session_id})
    assert shallow.structured_content == {
        "name": "some_list",
        "value": "[1, 2, 3]",
        "type": "list",
        "evaluate_name": "some_list",
        "children": [],
    }


async def test_evaluate_expression__deep(client: Client) -> None:
    session_id = await common_setup(client)
    deep = await client.call_tool(
        "evaluate_expression", {"expression": "some_object", "session_id": session_id, "depth": 4},
    )
    assert deep.structured_content == {
        "name": "some_object",
        "value": MatchRegex(r"<__main__\.Car object at 0x.+?>"),
        "type": "Car",
        "evaluate_name": "some_object",
        "children": [
            {
                "name": "color",
                "value": "<Color.RED: 'red'>",
                "type": "Color",
                "evaluate_name": "some_object.color",
                "children": [
                    {
                        "name": "name",
                        "value": "'RED'",
                        "type": "str",
                        "evaluate_name": "some_object.color.name",
                        "presentation_hint": {"attributes": ["rawString"]},
                        "children": None,
                    },
                    {
                        "name": "value",
                        "value": "'red'",
                        "type": "str",
                        "evaluate_name": "some_object.color.value",
                        "presentation_hint": {"attributes": ["rawString"]},
                        "children": None,
                    },
                ],
            },
            {
                "name": "doors",
                "value": MatchRegex(
                    r"\[<__main__\.Door object at 0x.+?>, <__main__\.Door object at 0x.+?>, <__main__\.Door object at 0x.+?>, <__main__\.Door object at 0x.+?>\]",
                ),
                "type": "list",
                "evaluate_name": "some_object.doors",
                "children": [
                    {
                        "name": "0",
                        "value": MatchRegex(r"<__main__\.Door object at 0x.+?>"),
                        "type": "Door",
                        "evaluate_name": "some_object.doors[0]",
                        "children": [
                            {
                                "name": "window",
                                "value": MatchRegex(
                                    r"<__main__\.Window object at 0x.+?>",
                                ),
                                "type": "Window",
                                "evaluate_name": "some_object.doors[0].window",
                                "children": [
                                    {
                                        "name": "state",
                                        "value": "'down'",
                                        "type": "str",
                                        "evaluate_name": "some_object.doors[0].window.state",
                                        "presentation_hint": {
                                            "attributes": ["rawString"],
                                        },
                                        "children": None,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "name": "1",
                        "value": MatchRegex(r"<__main__\.Door object at 0x.+?>"),
                        "type": "Door",
                        "evaluate_name": "some_object.doors[1]",
                        "children": [
                            {
                                "name": "window",
                                "value": MatchRegex(
                                    r"<__main__\.Window object at 0x.+?>",
                                ),
                                "type": "Window",
                                "evaluate_name": "some_object.doors[1].window",
                                "children": [
                                    {
                                        "name": "state",
                                        "value": "'down'",
                                        "type": "str",
                                        "evaluate_name": "some_object.doors[1].window.state",
                                        "presentation_hint": {
                                            "attributes": ["rawString"],
                                        },
                                        "children": None,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "name": "2",
                        "value": MatchRegex(r"<__main__\.Door object at 0x.+?>"),
                        "type": "Door",
                        "evaluate_name": "some_object.doors[2]",
                        "children": [
                            {
                                "name": "window",
                                "value": MatchRegex(
                                    r"<__main__\.Window object at 0x.+?>",
                                ),
                                "type": "Window",
                                "evaluate_name": "some_object.doors[2].window",
                                "children": [
                                    {
                                        "name": "state",
                                        "value": "'down'",
                                        "type": "str",
                                        "evaluate_name": "some_object.doors[2].window.state",
                                        "presentation_hint": {
                                            "attributes": ["rawString"],
                                        },
                                        "children": None,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "name": "3",
                        "value": MatchRegex(r"<__main__\.Door object at 0x.+?>"),
                        "type": "Door",
                        "evaluate_name": "some_object.doors[3]",
                        "children": [
                            {
                                "name": "window",
                                "value": MatchRegex(
                                    r"<__main__\.Window object at 0x.+?>",
                                ),
                                "type": "Window",
                                "evaluate_name": "some_object.doors[3].window",
                                "children": [
                                    {
                                        "name": "state",
                                        "value": "'down'",
                                        "type": "str",
                                        "evaluate_name": "some_object.doors[3].window.state",
                                        "presentation_hint": {
                                            "attributes": ["rawString"],
                                        },
                                        "children": None,
                                    },
                                ],
                            },
                        ],
                    },
                    {
                        "name": "len()",
                        "value": "4",
                        "type": "int",
                        "evaluate_name": "len(some_object.doors)",
                        "presentation_hint": {"attributes": ["readOnly"]},
                        "children": None,
                    },
                ],
            },
            {
                "name": "name",
                "value": "'Greased Lightning'",
                "type": "str",
                "evaluate_name": "some_object.name",
                "presentation_hint": {"attributes": ["rawString"]},
                "children": None,
            },
        ],
    }


async def test_evaluate_expression__hidden(client: Client) -> None:
    session_id = await common_setup(client)
    hidden = await client.call_tool(
        "evaluate_expression", {"expression": "some_list", "session_id": session_id, "show_hidden": True, "depth": 2},
    )
    some_list = hidden.structured_content

    # This dictionary, if printed, is 300 lines long.
    # We are not asserting on all that
    # Make some key asserts to prove the important structure is here

    # Check that our regular variables are still there
    assert some_list == {
        "name": "some_list",
        "value": "[1, 2, 3]",
        "type": "list",
        "evaluate_name": "some_list",
        "children": MatchAny(list),
    }

    # Check that special variables of regular variables are there
    assert some_list["children"][0] == {
        "name": "special variables", "value": "", "type": "", "children": MatchAny(list),
    }

    # Check that dunder properties of regular variables are there
    assert some_list["children"][0]["children"][1] == {
        "name": "__class__", "value": "<class 'list'>", "type": "type", "children": [],
    }

    # Check that function variables of regular variables are there
    assert some_list["children"][1] == {
        "name": "function variables", "value": "", "type": "", "children": MatchAny(list),
    }

    # Check that functions of regular variables are there
    assert some_list["children"][1]["children"][0] == {
        "name": "append",
        "value": MatchRegex(r"<built-in method append of list object at 0x.+?>"),
        "type": "builtin_function_or_method",
        "children": [],
    }


async def test_evaluate_expression__errors(client: Client) -> None:
    """
    Test that passing an invalid or useless expression to `evaluate_expression` doesn't raise a tool error.
    instead it returns the actual python error, as a value.
    """
    session_id = await common_setup(client)
    bad_syntax = await client.call_tool(
        "evaluate_expression", {"expression": "some_list[1", "session_id": session_id, "depth": 1},
    )
    assert bad_syntax.structured_content == {
        "name": "some_list[1",
        "value": "SyntaxError(\"'[' was never closed\", ('<string>', 1, 10, 'some_list[1', 1, 0))",
        "type": "SyntaxError",
        "evaluate_name": "some_list[1",
        "children": [
            {
                "name": "result",
                "value": "SyntaxError(\"'[' was never closed\", ('<string>', 1, 10, 'some_list[1', 1, 0))",
                "type": "SyntaxError",
                "evaluate_name": "some_list[1.result",
                "children": [],
            },
            {
                "name": "tb",
                "value": MatchRegex(r"<traceback object at 0x.+?>"),
                "type": "traceback",
                "evaluate_name": "some_list[1.tb",
                "children": [],
            },
        ],
    }

    nonexistent_variable = await client.call_tool(
        "evaluate_expression", {"expression": "sldkjf", "session_id": session_id},
    )
    assert nonexistent_variable.structured_content == {
        "name": "sldkjf",
        "value": "NameError(\"name 'sldkjf' is not defined\")",
        "type": "NameError",
        "evaluate_name": "sldkjf",
        "children": [],
    }

    empty_string = await client.call_tool("evaluate_expression", {"expression": "", "session_id": session_id})
    assert empty_string.structured_content == {
        "name": "",
        "value": "SyntaxError('invalid syntax', ('<string>', 0, 0, '', 0, 0))",
        "type": "SyntaxError",
        "evaluate_name": "",
        "children": [],
    }

    space = await client.call_tool("evaluate_expression", {"expression": " ", "session_id": session_id})
    assert space.structured_content == {
        "name": " ",
        "value": "IndentationError('unexpected indent', ('<string>', 1, 1, ' ', 1, -1))",
        "type": "IndentationError",
        "evaluate_name": " ",
        "children": [],
    }


async def test_evaluate_expression__specials(client: Client) -> None:
    session_id = await common_setup(client)
    """
    Test that passing an invalid or useless expression to `evaluate_expression` doesn't raise a tool error.
    instead it returns the actual python error, as a value.
    """
    dunder = await client.call_tool("evaluate_expression", {"expression": "__name__", "session_id": session_id})
    assert dunder.structured_content == {
        "name": "__name__",
        "value": "'__main__'",
        "type": "str",
        "evaluate_name": "__name__",
        "presentation_hint": {"attributes": ["rawString"]},
        "children": None,
    }

    clazz = await client.call_tool("evaluate_expression", {"expression": "Car", "session_id": session_id})
    assert clazz.structured_content == {
        "name": "Car",
        "value": "<class '__main__.Car'>",
        "type": "type",
        "evaluate_name": "Car",
        "children": [],
    }

    func = await client.call_tool("evaluate_expression", {"expression": "main", "session_id": session_id})
    assert func.structured_content == {
        "name": "main",
        "value": MatchRegex(r"<function main at 0x.+?>"),
        "type": "function",
        "evaluate_name": "main",
        "children": [],
    }


async def test_evaluate_expression__timeout(client: Client) -> None:
    session_id = (await create_session(client, file_path=FAKE_MAIN))["id"]

    await client.call_tool("run_to_line", {"session_id": session_id, "file_path": FAKE_MAIN, "line": 7})

    with pytest.raises(ToolError, match=r"timed out"):
        await client.call_tool(
            "evaluate_expression", {"expression": "sleep(1)", "session_id": session_id, "timeout": 100},
        )
