# JuneBug
This is a FastMCP server that allows an LLM to drive a Python debugger.
It was originally designed for Junie, the local JetBrains LLM harness, thus the name.

## The problem
LLMs cannot hold open a persistent TTY across conversational turns.
This is why you can't just point them at `pdb`, even though they know how to use it.
What they need is the ability to keep a Python process running in the background, with a DAP port open, and then send messages to that process over many LLM turns, so the LLM can think while it debugs.
Those messages need to be highly structured, so the LLM should not write them by hand.
Due to some idiocies of the DAP protocol, there's also a significant amount of state that a DAP client needs to track accurately across turns, which can't be directly retrieved from the DAP server.

## The solution
A locally running, persistent, HTTP based MCP server solves all these problems nicely.
It can launch Python processes, keep them open, close them if needed, and send correctly formatted DAP requests to them while they're running.
It can track the state that DAP requires, even when there are multiple simultaneous sessions on a single system.
It is also self-documenting, ideally requiring no skill or guidelines for any LLM to use.

## Doesn't that already exist?
IntelliJ Idea has a built-in MCP server that exposes this functionality, but it's exclusive to
1. Java
2. IntelliJ's UI, meaning that as the LLM is debugging, stuff moves around on the screen.

This is not how I want things to go, I want it to happen in the background, without the distraction and overhead of the UI.

## Features
1. Launch, attach, breakpoint, pause, resume, step, stack trace, thread dump, get variables, eval expressions, everything a debugger should do.
2. Multi-session support. Different LLMs (or even the same LLM) can have multiple debuggers attached to multiple processes simultaneously, without stepping on each other's toes.

## Planned features
1. Package this up as an extremely simple "double click it and it runs in your system tray" server, for Windows, Mac, and Linux.
2. Multi-language support, starting with Java.
