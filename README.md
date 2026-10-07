# JuneBug
This is a FastMCP server that allows an LLM to drive a Python debugger.
It was originally designed for Junie, the local JetBrains LLM harness, thus the name.

## The problem
LLMs cannot hold open a persistent TTY across conversational turns.
This is why you can't just point them at `pdb`, even though they know how to use it.
What they need is the ability to keep a Python process running in the background, with a DAP port open, and then send messages to that process over many LLM turns, so the LLM can think while it debugs. 

A locally running, persistent, HTTP based MCP server solves this problem neatly.
It can launch Python processes, keep them open, close them if needed, and send DAP requests to them while they're running.
Even better, IntelliJ Idea has already built an MCP server that exposes this kind of protocol, but it's exclusive to
1. Java
2. IntelliJ's UI, meaning that as the LLM is debugging, stuff moves around on the screen.

This is not how I want things to go, I want it to happen in the background, without the distraction and overhead of the UI.

## What I plan to do
1. Have Junie examine and copy the signatures of Intellij's debug MCP server.
2. Fill in those methods with actual functionality to do the python equivalent, using DAP as the underlying protocol.
3. Package this up as an extremely simple "double click it and it runs in your system tray" server, for Windows, Mac, and Linux.

## Features I want
1. Handle process management
2. Allow attaching to existing processes
3. Allow multi-client, multi-process support
4. Use a persistent DB of process info so that the server doesn't lose anything if it crashes or reboots
