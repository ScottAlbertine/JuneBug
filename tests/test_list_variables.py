from fastmcp import Client
from fastmcp.exceptions import ToolError
import pytest

from tests.constants import FAKE_MAIN, FAKE_MAIN_WITH_IMPORT, FAKE_MAIN_WITH_VARIABLES
from tests.utils import MatchAny, MatchRegex, create_session, move_to_next_breakpoint


async def common_setup(client: Client) -> str:
    """
    A bunch of tests in this file use intentionally identical setup, and are read-only, so they don't alter the setup at all.
    This handles that setup for them.
    """
    session_id = (await create_session(client, file_path=FAKE_MAIN_WITH_VARIABLES))["id"]
    await client.call_tool(
        "set_breakpoint", {"session_id": session_id, "file_path": FAKE_MAIN_WITH_VARIABLES, "line": 38},
    )
    await move_to_next_breakpoint(client, session_id)
    return session_id


async def test_list_variables__invalid(client: Client) -> None:
    session_id = await common_setup(client)
    with pytest.raises(ToolError, match=r"Stack frame 999999 was not found\."):
        await client.call_tool("list_variables", {"session_id": session_id, "frame_id": 999999})

    with pytest.raises(ToolError, match=r"timeout\n.+Input should be greater than or equal to 0"):
        await client.call_tool("list_variables", {"session_id": session_id, "timeout": -1})

    with pytest.raises(ToolError, match=r"depth\n.+Input should be greater than or equal to 0"):
        await client.call_tool("list_variables", {"session_id": session_id, "depth": -1})

    with pytest.raises(ToolError, match=r"depth\n.+Input should be less than or equal to 4"):
        await client.call_tool("list_variables", {"session_id": session_id, "depth": 5})


async def test_list_variables__not_top_frame(client: Client) -> None:
    """Test that we can specify a frame that's not the top of the stack, and get variables for it."""
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

    # Check its variables
    variables = await client.call_tool("list_variables", {"session_id": session_id, "frame_id": frame_id})
    assert variables.structured_content == {
        "variables": [
            {
                "name": "function_scoped_string",
                "value": "'in here'",
                "type": "str",
                "evaluate_name": "function_scoped_string",
                "presentation_hint": {"attributes": ["rawString"]},
                "children": None,
            },
            {
                "name": "module_scoped_string",
                "value": "'out here'",
                "type": "str",
                "evaluate_name": "module_scoped_string",
                "presentation_hint": {"attributes": ["rawString"]},
                "children": None,
            },
        ],
    }

    # Pick the first frame ID
    frame_id = stack.structured_content["frames"][0]["id"]

    # Check its variables
    variables = await client.call_tool("list_variables", {"session_id": session_id, "frame_id": frame_id})
    assert variables.structured_content == {
        "variables": [
            {"name": "a", "value": "2", "type": "int", "evaluate_name": "a", "children": None},
            {"name": "b", "value": "3", "type": "int", "evaluate_name": "b", "children": None},
        ],
    }


async def test_list_variables__not_paused(client: Client) -> None:
    """Test that you get an appropriate error if you try to list variables when you're not paused"""
    session_id = (await create_session(client, file_path=FAKE_MAIN, program_arguments=["--loop-forever"]))["id"]

    await client.call_tool("control_debugger_session", {"session_id": session_id, "action": "resume"})

    with pytest.raises(ToolError, match=r"Session must be paused to call that tool. Session is currently running."):
        await client.call_tool("list_variables", {"session_id": session_id})


async def test_list_variables__shallow(client: Client) -> None:
    session_id = await common_setup(client)
    shallow = await client.call_tool("list_variables", {"session_id": session_id})
    assert shallow.structured_content == {
        "variables": [
            {"name": "some_bool", "value": "True", "type": "bool", "evaluate_name": "some_bool", "children": None},
            {
                "name": "some_dict",
                "value": "{'a': 1, 'b': 2, 'c': 3}",
                "type": "dict",
                "evaluate_name": "some_dict",
                "children": [],
            },
            {
                "name": "some_enum",
                "value": "<Color.RED: 'red'>",
                "type": "Color",
                "evaluate_name": "some_enum",
                "children": [],
            },
            {"name": "some_float", "value": "1.23", "type": "float", "evaluate_name": "some_float", "children": None},
            {"name": "some_int", "value": "123", "type": "int", "evaluate_name": "some_int", "children": None},
            {"name": "some_list", "value": "[1, 2, 3]", "type": "list", "evaluate_name": "some_list", "children": []},
            {
                "name": "some_object",
                "value": MatchRegex(r"<__main__\.Car object at 0x.+?>"),
                "type": "Car",
                "evaluate_name": "some_object",
                "children": [],
            },
            {
                "name": "some_string",
                "value": "'some string'",
                "type": "str",
                "evaluate_name": "some_string",
                "presentation_hint": {"attributes": ["rawString"]},
                "children": None,
            },
            {
                "name": "some_tuple",
                "value": "(1, 2, 3)",
                "type": "tuple",
                "evaluate_name": "some_tuple",
                "children": [],
            },
        ],
    }


async def test_list_variables__deep(client: Client) -> None:
    session_id = await common_setup(client)
    deep = await client.call_tool("list_variables", {"session_id": session_id, "depth": 4})
    assert deep.structured_content == {
        "variables": [
            {"name": "some_bool", "value": "True", "type": "bool", "evaluate_name": "some_bool", "children": None},
            {
                "name": "some_dict",
                "value": "{'a': 1, 'b': 2, 'c': 3}",
                "type": "dict",
                "evaluate_name": "some_dict",
                "children": [
                    {"name": "'a'", "value": "1", "type": "int", "evaluate_name": "some_dict['a']", "children": None},
                    {"name": "'b'", "value": "2", "type": "int", "evaluate_name": "some_dict['b']", "children": None},
                    {"name": "'c'", "value": "3", "type": "int", "evaluate_name": "some_dict['c']", "children": None},
                    {
                        "name": "len()",
                        "value": "3",
                        "type": "int",
                        "evaluate_name": "len(some_dict)",
                        "presentation_hint": {"attributes": ["readOnly"]},
                        "children": None,
                    },
                ],
            },
            {
                "name": "some_enum",
                "value": "<Color.RED: 'red'>",
                "type": "Color",
                "evaluate_name": "some_enum",
                "children": [
                    {
                        "name": "name",
                        "value": "'RED'",
                        "type": "str",
                        "evaluate_name": "some_enum.name",
                        "presentation_hint": {"attributes": ["rawString"]},
                        "children": None,
                    },
                    {
                        "name": "value",
                        "value": "'red'",
                        "type": "str",
                        "evaluate_name": "some_enum.value",
                        "presentation_hint": {"attributes": ["rawString"]},
                        "children": None,
                    },
                ],
            },
            {"name": "some_float", "value": "1.23", "type": "float", "evaluate_name": "some_float", "children": None},
            {"name": "some_int", "value": "123", "type": "int", "evaluate_name": "some_int", "children": None},
            {
                "name": "some_list",
                "value": "[1, 2, 3]",
                "type": "list",
                "evaluate_name": "some_list",
                "children": [
                    {"name": "0", "value": "1", "type": "int", "evaluate_name": "some_list[0]", "children": None},
                    {"name": "1", "value": "2", "type": "int", "evaluate_name": "some_list[1]", "children": None},
                    {"name": "2", "value": "3", "type": "int", "evaluate_name": "some_list[2]", "children": None},
                    {
                        "name": "len()",
                        "value": "3",
                        "type": "int",
                        "evaluate_name": "len(some_list)",
                        "presentation_hint": {"attributes": ["readOnly"]},
                        "children": None,
                    },
                ],
            },
            {
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
                                        "value": MatchRegex(r"<__main__\.Window object at 0x.+?>"),
                                        "type": "Window",
                                        "evaluate_name": "some_object.doors[0].window",
                                        "children": [
                                            {
                                                "name": "state",
                                                "value": "'down'",
                                                "type": "str",
                                                "evaluate_name": "some_object.doors[0].window.state",
                                                "presentation_hint": {"attributes": ["rawString"]},
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
                                        "value": MatchRegex(r"<__main__\.Window object at 0x.+?>"),
                                        "type": "Window",
                                        "evaluate_name": "some_object.doors[1].window",
                                        "children": [
                                            {
                                                "name": "state",
                                                "value": "'down'",
                                                "type": "str",
                                                "evaluate_name": "some_object.doors[1].window.state",
                                                "presentation_hint": {"attributes": ["rawString"]},
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
                                        "value": MatchRegex(r"<__main__\.Window object at 0x.+?>"),
                                        "type": "Window",
                                        "evaluate_name": "some_object.doors[2].window",
                                        "children": [
                                            {
                                                "name": "state",
                                                "value": "'down'",
                                                "type": "str",
                                                "evaluate_name": "some_object.doors[2].window.state",
                                                "presentation_hint": {"attributes": ["rawString"]},
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
                                        "value": MatchRegex(r"<__main__\.Window object at 0x.+?>"),
                                        "type": "Window",
                                        "evaluate_name": "some_object.doors[3].window",
                                        "children": [
                                            {
                                                "name": "state",
                                                "value": "'down'",
                                                "type": "str",
                                                "evaluate_name": "some_object.doors[3].window.state",
                                                "presentation_hint": {"attributes": ["rawString"]},
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
            },
            {
                "name": "some_string",
                "value": "'some string'",
                "type": "str",
                "evaluate_name": "some_string",
                "presentation_hint": {"attributes": ["rawString"]},
                "children": None,
            },
            {
                "name": "some_tuple",
                "value": "(1, 2, 3)",
                "type": "tuple",
                "evaluate_name": "some_tuple",
                "children": [
                    {"name": "0", "value": "1", "type": "int", "evaluate_name": "some_tuple[0]", "children": None},
                    {"name": "1", "value": "2", "type": "int", "evaluate_name": "some_tuple[1]", "children": None},
                    {"name": "2", "value": "3", "type": "int", "evaluate_name": "some_tuple[2]", "children": None},
                    {
                        "name": "len()",
                        "value": "3",
                        "type": "int",
                        "evaluate_name": "len(some_tuple)",
                        "presentation_hint": {"attributes": ["readOnly"]},
                        "children": None,
                    },
                ],
            },
        ],
    }


async def test_list_variables__hidden(client: Client) -> None:
    session_id = await common_setup(client)
    hidden = await client.call_tool(
        "list_variables", {"session_id": session_id, "show_hidden": True, "depth": 2},
    )

    # This dictionary, if printed, is 2,900 lines long.
    # We are not asserting on all that
    # Make some key asserts to prove the important structure is here
    variables = hidden.structured_content["variables"]

    # Check that our regular variables are still there
    assert variables[0] == {
        "name": "some_bool", "value": "True", "type": "bool", "evaluate_name": "some_bool", "children": None,
    }

    # Check that special variables of regular variables are there
    assert variables[1]["children"][0] == {
        "name": "special variables", "value": "", "type": "", "children": MatchAny(list),
    }

    # Check that dunder properties of regular variables are there
    assert variables[1]["children"][0]["children"][0] == {
        "name": "__class__", "value": "<class 'dict'>", "type": "type", "children": [],
    }

    # Check that function variables of regular variables are there
    assert variables[1]["children"][1] == {
        "name": "function variables", "value": "", "type": "", "children": MatchAny(list),
    }

    # Check that functions of regular variables are there
    assert variables[1]["children"][1]["children"][0] == {
        "name": "clear",
        "value": MatchRegex(r"<built-in method clear of dict object at 0x.+?>"),
        "type": "builtin_function_or_method",
        "children": MatchAny(list),
    }

    # Check that global special variables are there
    assert variables[9] == {"name": "special variables", "value": "", "type": "", "children": MatchAny(list)}

    # Check that special variables of special variables are there, though not fully populated at this depth
    assert variables[9]["children"][0]["children"][0] == {
        "name": "special variables", "value": "", "type": "", "children": [],
    }

    # Check that function variables of special variables are there, also not populated at this depth
    assert variables[9]["children"][0]["children"][1] == {
        "name": "function variables", "value": "", "type": "", "children": [],
    }

    # Check that global dunder properties are there
    assert variables[9]["children"][5] == {
        "name": "__name__",
        "value": "'__main__'",
        "type": "str",
        "presentation_hint": {"attributes": ["rawString"]},
        "children": None,
    }

    # Check that global function variables are there
    assert variables[10] == {
        "name": "function variables",
        "value": "",
        "type": "",
        "children": [
            {
                "name": "main",
                "value": MatchRegex(r"<function main at 0x.+?>"),
                "type": "function",
                "children": [{"name": "special variables", "value": "", "type": "", "children": []}],
            },
        ],
    }

    # Check that global class variables are there
    assert variables[11] == {"name": "class variables", "value": "", "type": "", "children": MatchAny(list)}

    # Check that global class variables defined in the file are populated, with their special variables available
    assert variables[11]["children"][0] == {
        "name": "Car",
        "value": "<class '__main__.Car'>",
        "type": "type",
        "children": [{"name": "special variables", "value": "", "type": "", "children": []}],
    }

    # Check that global class variables that are just imported, not defined in here, are populated
    assert variables[11]["children"][3] == {
        "name": "Enum",
        "value": "<enum 'Enum'>",
        "type": "EnumType",
        "children": [{"name": "special variables", "value": "", "type": "", "children": []}],
    }


async def test_list_variables__timeout(client: Client) -> None:
    session_id = await common_setup(client)
    with pytest.raises(ToolError, match=r"timed out"):
        await client.call_tool(
            "list_variables", {"session_id": session_id, "depth": 4, "show_hidden": True, "timeout": 100},
        )
    # Check that you can retry the call, and it works
    actual = await client.call_tool("list_variables", {"session_id": session_id})
    assert actual.structured_content["variables"][1]["value"] == "{'a': 1, 'b': 2, 'c': 3}"
