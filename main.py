from fastmcp import FastMCP

from tools import (
    control_session,
    evaluate_expression,
    get_debugger_session,
    get_frame_values,
    get_stack,
    get_threads,
    get_value_by_path,
    list_breakpoints,
    list_debugger_sessions,
    remove_breakpoint,
    run_to_line,
    set_breakpoint,
    set_breakpoints_muted,
    set_variable,
    start_debugger_session,
)

# TODO: update the server description, and any other params that the intellij original specifies on this call
mcp = FastMCP("JuneBug MCP Server")

mcp.tool(control_session)
mcp.tool(evaluate_expression)
mcp.tool(get_debugger_session)
mcp.tool(get_frame_values)
mcp.tool(get_stack)
mcp.tool(get_threads)
mcp.tool(get_value_by_path)
mcp.tool(list_breakpoints)
mcp.tool(list_debugger_sessions)
mcp.tool(remove_breakpoint)
mcp.tool(run_to_line)
mcp.tool(set_breakpoint)
mcp.tool(set_breakpoints_muted)
mcp.tool(set_variable)
mcp.tool(start_debugger_session)

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=9000)
