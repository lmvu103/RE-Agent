import streamlit as st
import asyncio
import os
import sys
import threading
from concurrent.futures import Future
from streamlit.runtime.scriptrunner import add_script_run_ctx
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

# Path configuration
PYTHON_UV = sys.executable 
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_DIR = os.path.join(ROOT_DIR, "mcp_server")

def get_mcp_server_params():
    return StdioServerParameters(command=PYTHON_UV, args=[os.path.join(MCP_DIR, "server.py")])

async def get_all_tools():
    params = get_mcp_server_params()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await session.list_tools()
            return response.tools

async def call_mcp_tool(name: str, arguments: dict):
    params = get_mcp_server_params()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.call_tool(name, arguments=arguments)

def run_sync(coro_func, *args, **kwargs):
    future = Future()
    def target():
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(coro_func(*args, **kwargs))
            future.set_result(result)
        except Exception as e: future.set_exception(e)
        finally: loop.close()
    thread = threading.Thread(target=target)
    add_script_run_ctx(thread)
    thread.start()
    return future.result()
