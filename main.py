from pathlib import Path
from threading import Thread

from PIL import Image
from fastmcp import FastMCP
import pyperclip
from pystray import Icon, Menu, MenuItem
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from tools import (
    attach_debugger_session,
    control_debugger_session,
    evaluate_expression,
    get_debugger_session,
    get_stack,
    launch_debugger_session,
    list_breakpoints,
    list_debugger_sessions,
    list_threads,
    list_variables,
    remove_breakpoint,
    run_to_line,
    set_breakpoint,
    set_breakpoints_muted,
)

HOST = "127.0.0.1"
PORT = 20561
URL = f"http://{HOST}:{PORT}/mcp"

mcp = FastMCP("JuneBug MCP Server")

mcp.tool(attach_debugger_session)
mcp.tool(control_debugger_session)
mcp.tool(evaluate_expression)
mcp.tool(get_debugger_session)
mcp.tool(get_stack)
mcp.tool(launch_debugger_session)
mcp.tool(list_breakpoints)
mcp.tool(list_debugger_sessions)
mcp.tool(list_threads)
mcp.tool(list_variables)
mcp.tool(remove_breakpoint)
mcp.tool(run_to_line)
mcp.tool(set_breakpoint)
mcp.tool(set_breakpoints_muted)


def run_mcp_server() -> None:
    mcp.run(
        transport="http",
        show_banner=False,
        host=HOST,
        port=PORT,
        middleware=[Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])],
        stateless_http=True,
    )


if __name__ == "__main__":
    Thread(target=run_mcp_server).start()

    icon = Icon(
        "JuneBug",
        Image.open(Path(__file__).with_name("icon.png")),
        "JuneBug",
        Menu(
            MenuItem("JuneBug MCP server is running.", lambda: None, enabled=False),
            MenuItem(f"Available at {URL}", lambda: None, enabled=False),
            MenuItem("Click here to copy that URL to your clipboard.", lambda: pyperclip.copy(URL)),
            Menu.SEPARATOR,
            MenuItem('Quit', lambda i, _: i.stop()),
        ),
    )
    # Sadly, this is a UI thing, and requires running on (and blocking) the main thread.
    icon.run()
