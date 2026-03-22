import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession

import os
import sys
import threading
from concurrent.futures import Future
from streamlit.runtime.scriptrunner import add_script_run_ctx

# -----------------
# Premium Custom Component v2 (CCv2)
# -----------------
_PREMIUM_HEADER = st.components.v2.component(
    "pyres_header",
    html="""
    <div class="header-container">
        <div class="logo-area">
            <span class="logo-icon">🚀</span>
            <div class="logo-text">
                <div class="main-title">PERE Agents</div>
                <div class="sub-title">Reservoir Engineering Assistant</div>
            </div>
        </div>
        <div class="status-area">
            <div class="status-chip" id="model-chip">
                <span class="label">MODEL</span>
                <span class="value">...</span>
            </div>
            <div class="status-chip" id="tools-chip">
                <span class="label">TOOLS</span>
                <span class="value">...</span>
            </div>
            <div class="status-chip reset-chip" id="reset-chip">
                <span class="label">ACTIONS</span>
                <span class="value">Reset Chat</span>
            </div>
        </div>
    </div>
    """,
    css="""
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.5rem;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        margin-bottom: 1.5rem;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        color: var(--st-text-color);
    }
    .logo-area {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .logo-icon {
        font-size: 2rem;
        filter: drop-shadow(0 0 8px rgba(79, 172, 254, 0.5));
    }
    .main-title {
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-title {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--st-secondary-text-color);
        opacity: 0.8;
    }
    .status-area {
        display: flex;
        gap: 0.75rem;
    }
    .status-chip {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        background: rgba(0, 0, 0, 0.2);
        padding: 6px 14px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .reset-chip {
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 69, 58, 0.1);
    }
    .reset-chip:hover {
        background: rgba(255, 69, 58, 0.1);
        border-color: rgba(255, 69, 58, 0.4);
        transform: translateY(-1px);
    }
    .status-chip .label {
        font-size: 0.6rem;
        font-weight: 700;
        color: var(--st-secondary-text-color);
        margin-bottom: 2px;
        pointer-events: none;
    }
    .status-chip .value {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--st-primary-color);
        pointer-events: none;
    }
    .reset-chip .value {
        color: #ff453a !important;
    }
    """,
    js="""
    export default function (component) {
        const { data, parentElement, setTriggerValue } = component
        if (!data) return
        
        const modelVal = parentElement.querySelector("#model-chip .value")
        const toolsVal = parentElement.querySelector("#tools-chip .value")
        const resetBtn = parentElement.querySelector("#reset-chip")
        
        if (modelVal) modelVal.textContent = (data.model || "None").replace("models/", "")
        if (toolsVal) toolsVal.textContent = data.toolCount || "0"
        
        if (resetBtn) {
            resetBtn.onclick = () => {
                setTriggerValue("reset", true)
            }
        }
    }
    """
)

# Path configuration
PYTHON_UV = sys.executable 
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_DIR = os.path.join(ROOT_DIR, "mcp_server")

SYSTEM_PROMPT = """You are an expert Petroleum Engineering AI Assistant (PERE Agents).
Use provided tools to perform reservoir engineering calculations.
Always provide a JSON block at the VERY END for tabular/chart data.
Table: {"plot_type": "table", "data": {"Col": []}}
Chart: {"plot_type": "line", "x_label": "X", "y_label": "Y", "series": {"S1": {"x": [], "y": []}}}
"""

# -----------------
# Configuration
# -----------------
API_KEY_DEFAULT = st.secrets.get("GEMINI_API_KEY", "")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

with st.sidebar:
    st.header("⚙️ Agent Settings")
    API_KEY = st.text_input("Gemini API Key", value=API_KEY_DEFAULT, type="password")
    MODEL_NAME = st.selectbox("Gemini Model", [
        "gemini-2.5-flash", "gemini-2.0-flash", "gemini-3-flash-preview", "gemini-flash-latest"
    ])
    st.divider()
    with st.expander("💡 Helper Tools", expanded=False):
        st.markdown("- IPR Curves\n- PVT properties\n- Nodal Analysis\n- DCA Forecasting")

# -----------------
# MCP Helpers
# -----------------
@st.cache_resource
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

# Tool Loading
if "openai_tools" not in st.session_state:
    try:
        tools_list = run_sync(get_all_tools)
        st.session_state.openai_tools = [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}} for t in tools_list]
    except Exception as e:
        st.error(f"MCP Connection Error: {e}")
        st.stop()

openai_tools = st.session_state.openai_tools

# -----------------
# Chat Logic
# -----------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

def display_msg(m, key_suffix=""):
    role, content = m.get("role"), m.get("content", "")
    avatar = "🤖" if role == "assistant" else "👤"
    
    if isinstance(m.get("tool_calls"), list):
        func_names = [tc["function"]["name"] for tc in m["tool_calls"]]
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(f"🛠️ **PERE Agents** utilized tools: `{', '.join(func_names)}`")
        return

    with st.chat_message(role, avatar=avatar):
        if role == "assistant" and "```json" in content:
            idx = content.rfind("```json")
            st.markdown(content[:idx].strip())
            try:
                data = json.loads(content[idx+7 : content.rfind("```")].strip())
                if data.get("plot_type") == "table":
                    df = pd.DataFrame(data.get("data", {}))
                    st.dataframe(df, use_container_width=True)
                    st.download_button("📥 CSV", df.to_csv(index=False), f"data_{key_suffix}.csv", key=f"dl_{key_suffix}")
                elif data.get("plot_type") == "line":
                    fig = go.Figure()
                    for s_n, s_d in data.get("series", {}).items():
                        fig.add_trace(go.Scatter(x=s_d["x"], y=s_d["y"], name=s_n))
                    st.plotly_chart(fig, use_container_width=True)
            except: st.code(content[idx:])
        else: st.markdown(content)

def _chat_with_agent(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    
    with st.chat_message("assistant", avatar="🤖"):
        with st.status("🚀 Analyzing engineering data...", expanded=True) as status:
            messages_for_api = [{"role": m["role"], "content": m.get("content", ""), "tool_calls": m.get("tool_calls"), "tool_call_id": m.get("tool_call_id"), "name": m.get("name")} for m in st.session_state.messages]
            
            try:
                response = client.chat.completions.create(model=MODEL_NAME, messages=messages_for_api, tools=openai_tools, tool_choice="auto")
                resp = response.choices[0].message
                
                while resp.tool_calls:
                    st.session_state.messages.append({"role": "assistant", "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in resp.tool_calls]})
                    for tc in resp.tool_calls:
                        status.update(label=f"⚙️ Running tool: {tc.function.name}")
                        res = run_sync(call_mcp_tool, tc.function.name, json.loads(tc.function.arguments))
                        st.session_state.messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": "\n".join([c.text for c in res.content if getattr(c, 'type', '') == 'text']) or str(res.content)})
                    
                    messages_for_api = [{"role": m["role"], "content": m.get("content", ""), "tool_calls": m.get("tool_calls"), "tool_call_id": m.get("tool_call_id"), "name": m.get("name")} for m in st.session_state.messages]
                    response = client.chat.completions.create(model=MODEL_NAME, messages=messages_for_api, tools=openai_tools)
                    resp = response.choices[0].message
                
                st.session_state.messages.append({"role": "assistant", "content": resp.content})
                status.update(label="✅ Complete", state="complete", expanded=False)
            except Exception as e: st.error(f"Agent Error: {e}")

# -----------------
# Main Layout
# -----------------
header_result = _PREMIUM_HEADER(data={"model": MODEL_NAME, "toolCount": len(openai_tools)}, key="header")
if getattr(header_result, "reset", False):
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.rerun()

tab_chat, tab_guide = st.tabs(["💬 AI Agent", "📖 User Guide"])

with tab_chat:
    # 0. Submission Logic (Top level of tab to update state BEFORE rendering)
    with st.container(border=True):
        prompt = st.text_input("Technical Query:", placeholder="Enter command...", label_visibility="collapsed", key="v9_input")
        if st.button("🔄 Reset Chat", key="reset_v9") or getattr(header_result, "reset", False):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.rerun()

    # Process new prompt
    if prompt and ("p_v9" not in st.session_state or st.session_state.p_v9 != prompt):
        st.session_state.p_v9 = prompt
        _chat_with_agent(prompt)
        st.rerun()

    # 1. Message Management (Now reflects the LATEST result)
    all_msgs = [m for m in st.session_state.messages if m["role"] != "system" and m["role"] != "tool"]
    last_u_idx = next((i for i in range(len(all_msgs)-1, -1, -1) if all_msgs[i]["role"] == "user"), -1)
    
    if last_u_idx != -1:
        hist = all_msgs[:last_u_idx]
        active = all_msgs[last_u_idx:]
    else:
        hist = all_msgs
        active = []

    # 2. History Area (Scrollable Top)
    if hist:
        for i, m in enumerate(hist):
            display_msg(m, f"h_{i}")
        st.divider()

    # 3. Active Results Area (Bottom)
    if active:
        for i, m in enumerate(active):
            if m["role"] == "assistant" and i == len(active)-1:
                st.caption("Latest Final Answer:")
            display_msg(m, f"a_{i}")
    
    # Onboarding
    if not all_msgs:
        sel = st.pills("Start with:", ["📈 Vogel IPR Curve", "🧪 Oil PVT Properties", "☁️ Z-Factor Calculation"])
        if sel:
            _chat_with_agent(sel)
            st.rerun()

with tab_guide:
    st.header("📖 Technical Guide")
    st.markdown("Professional tools for Reservoir and Production Engineers.")
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("🧪 PVT", expanded=True): st.write("- Oil & Gas properties\n- S-W Brine model")
        with st.expander("📈 IPR"): st.write("- Vogel & Radial flow\n- Horizontal wells")
    with c2:
        with st.expander("📉 Decline Curve"): st.write("- Arps and Duong models")
        with st.expander("⚒️ Geomechanics"): st.write("- Pore pressure & Stress")
