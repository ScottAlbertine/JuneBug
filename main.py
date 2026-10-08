from fastmcp import FastMCP

from tools import (
    xdebug_control_session,
    xdebug_evaluate_expression,
    xdebug_get_debugger_status,
    xdebug_get_frame_values,
    xdebug_get_stack,
    xdebug_get_threads,
    xdebug_get_value_by_path,
    xdebug_list_breakpoints,
    xdebug_remove_breakpoint,
    xdebug_run_to_line,
    xdebug_set_breakpoint,
    xdebug_set_variable,
    xdebug_start_debugger_session,
)

# TODO: dedupe a bunch of these annotated strings, there's a lot of repeats
# TODO: turn the response dicts into response objects, after reading up on how to do so on the FastMCP docs

# TODO: update the server description, and any other params that the intellij original specifies on this call
mcp = FastMCP("JuneBug MCP Server")

# TODO: take off the xdebug prefix, since we don't have anything else in here, it might not be needed

mcp.tool(xdebug_control_session)
mcp.tool(xdebug_evaluate_expression)
mcp.tool(xdebug_get_debugger_status)
mcp.tool(xdebug_get_frame_values)
mcp.tool(xdebug_get_stack)
mcp.tool(xdebug_get_threads)
mcp.tool(xdebug_get_value_by_path)
mcp.tool(xdebug_list_breakpoints)
mcp.tool(xdebug_remove_breakpoint)
mcp.tool(xdebug_run_to_line)
mcp.tool(xdebug_set_breakpoint)
mcp.tool(xdebug_set_variable)
mcp.tool(xdebug_start_debugger_session)

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=9000)
