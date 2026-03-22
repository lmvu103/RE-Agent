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
# Define a sleek glassmorphic header component
_PREMIUM_HEADER = st.components.v2.component(
    "pyres_header",
    html="""
    <div class="header-container">
        <div class="logo-area">
            <span class="logo-icon">🚀</span>
            <div class="logo-text">
                <div class="main-title">pyResToolbox AI</div>
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
        </div>
    </div>
    """,
    css=\"\"\"
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
    .status-chip .label {
        font-size: 0.6rem;
        font-weight: 700;
        color: var(--st-secondary-text-color);
        margin-bottom: 2px;
    }
    .status-chip .value {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--st-primary-color);
    }
    \"\"\",
    js="""
    export default function (component) {
        const { data, parentElement } = component
        if (!data) return
        
        const modelVal = parentElement.querySelector("#model-chip .value")
        const toolsVal = parentElement.querySelector("#tools-chip .value")
        
        if (modelVal) modelVal.textContent = (data.model || "None").replace("models/", "")
        if (toolsVal) toolsVal.textContent = data.toolCount || "0"
    }
    """
)

# Path configuration for the pyrestoolbox MCP Server
PYTHON_UV = sys.executable 
# Use absolute paths based on app.py location
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_DIR = os.path.join(ROOT_DIR, "mcp_server")
SYSTEM_PROMPT = """You are an expert Petroleum Engineering AI Assistant equipped with the pyResToolbox tools via the Model Context Protocol (MCP).
You can calculate PVT properties, generate IPR curves, black oil tables, and perform various other reservoir engineering tasks.
Use the provided tools to fulfill the user requests. You can execute multiple tool calls sequentially if needed.

IMPORTANT PLOTTING/TABLULAR INSTRUCTIONS:
Always provide a JSON block at the VERY END of your response for any tabular or chart data.
Format for tables: {"plot_type": "table", "data": {"Column": [values]}}
Format for charts: {"plot_type": "line", "x_label": "X", "y_label": "Y", "series": {"Name": {"x": [], "y": []}}}
"""

# -----------------
# Configuration (Google Gemini / Google AI Studio)
# -----------------
# DEFAULT API KEY from user (Recommendation: do NOT hardcode keys!)
API_KEY_DEFAULT = st.secrets.get("GEMINI_API_KEY", "")
# Google's OpenAI-compatible endpoint
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

with st.sidebar:
    st.header("⚙️ Agent Settings")
    API_KEY = st.text_input("Google AI Studio (Gemini) API Key", value=API_KEY_DEFAULT, type="password", help="Enter your Gemini key here.")
    MODEL_NAME = st.selectbox("Gemini Model", [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-3-flash-preview",
        "gemini-flash-latest",
        "gemini-2.5-pro"
    ], help="Select which Gemini model to use.")
    AGENT_NAME = st.text_input("Agent Display Name", value="pyResToolbox AI")
    
    if not API_KEY:
        st.warning("⚠️ Google Gemini API Key missing!")
    else:
        st.success("App connected to Gemini AI ✅")

    st.divider()
    
    st.divider()
    with st.expander("💡 Example Queries", expanded=True):
        st.markdown("""
        - **IPR Curve**: 
          *"Generate IPR for Pi=4000, Pb=3500, IPR_Model=Vogel, J=1.2"*
        - **PVT Properties**: 
          *"Calculate oil PVT for 200°F, 3000 psia, API 35, Gas Gravity 0.7"*
        - **Gas Properties**: 
          *"Find Z-Factor and gas density at 4200 psia, 180°F, 0.65 gravity"*
        - **Tools Info**: 
          *"What engineering calculations can you perform?"*
        """)
    
    st.divider()
    st.markdown("### User Context")
    user_context = st.text_area("Optional: Paste JSON/CSV context", help="Data here will be used by the agent.")

# -----------------
# MCP Helpers
# -----------------
@st.cache_resource
def get_mcp_server_params():
    return StdioServerParameters(
        command=PYTHON_UV,
        args=[os.path.join(MCP_DIR, "server.py")],
    )

async def get_all_tools():
    params = get_mcp_server_params()
    try:
        # Increase connection timeout or handle it gracefully
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                return response.tools
    except Exception as e:
        # Better diagnostic info: reveal WHAT the server is actually complaining about
        import os
        cwd = os.getcwd()
        mcp_exists = os.path.exists(MCP_DIR)
        server_path = os.path.join(MCP_DIR, "server.py")
        server_exists = os.path.exists(server_path)
        diag_msg = f"\nDiagnostic Info: CWD={cwd}, MCP_DIR={MCP_DIR} (exists={mcp_exists}), server.py={server_path} (exists={server_exists})"
        
        # Try to run the server for just 2 seconds to capture its startup errors (like ImportErrors)
        import subprocess
        try:
            # We use a short timeout (3s) and don't expect it to finish (it's a server)
            # but we catch even the errors it prints before hanging
            diag = subprocess.run([params.command] + params.args, capture_output=True, text=True, timeout=3)
            # If it finished, something is definitely wrong (server should run forever)
            error_msg = f"Server exited unexpectedly: {e}{diag_msg}\n\nStdout: {diag.stdout}\nStderr: {diag.stderr}"
        except subprocess.TimeoutExpired as te:
            # This is expected for a working server! So let's see what it printed in those 3 seconds
            stderr = (te.stderr or "").strip()
            stdout = (te.stdout or "").strip()
            if stderr or stdout:
                 error_msg = f"Failed to list tools (Server seems to start but failed to communicate): {e}{diag_msg}\n\nServer output in first 3s:\nSTDOUT: {stdout}\nSTDERR: {stderr}"
            else:
                 error_msg = f"Failed to list tools (Server started but NO output): {e}{diag_msg}"
        except Exception as diag_e:
            error_msg = f"Failed to list tools: {e}{diag_msg}\n\nDiagnostic failure: {diag_e}"
        raise Exception(error_msg)

async def call_mcp_tool(name: str, arguments: dict):
    params = get_mcp_server_params()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments=arguments)
            return result

# -----------------
# Async Helper (Isolated Execution)
# -----------------
def run_sync(coro_func, *args, **kwargs):
    """Run a coroutine in a fresh thread/loop to isolate MCP IO from Streamlit."""
    future = Future()
    
    def target():
        import asyncio
        import anyio
        
        # Fresh loop for a fresh thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # anyio.run is great but it doesn't like existing threads sometimes.
            # Using loop.run_until_complete is more consistent for single tasks
            result = loop.run_until_complete(coro_func(*args, **kwargs))
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            loop.close()

    thread = threading.Thread(target=target)
    add_script_run_ctx(thread)
    thread.start()
    return future.result()

# Fetch tools once
if "openai_tools" not in st.session_state:
    try:
        with st.spinner("Connecting to pyResToolbox MCP server... Loading all 108 engineering tools."):
            # Use our robust helper, pass the FUNCTION, not the coroutine object
            tools_list = run_sync(get_all_tools)
            
            openai_tools = []
            for t in tools_list:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema
                    }
                })
            st.session_state.openai_tools = openai_tools
    except Exception as e:
        st.error(f"Error connecting to local MCP Server: {e}\n\nMake sure UV is installed and the directory is correct.")
        st.stop()
else:
    openai_tools = st.session_state.openai_tools

    st.info("👋 Hello! I am your Petroleum AI. How can I help you today?")
    
# -----------------
# UI Chat State
# -----------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# -----------------
# Suggestion Chips (Onboarding)
# -----------------
SUGGESTIONS = {
    "📈 Vogel IPR Curve": "Generate IPR for Pi=4000, Pb=3500, IPR_Model=Vogel, J=1.2. Plot the results.",
    "🧪 Oil PVT (Standing)": "Calculate oil PVT properties using Standing correlation for 200°F, 3000 psia, API 35, Gas Gravity 0.7.",
    "☁️ Gas Z-Factor": "Find gas Z-factor (DAK) at 4000 psia, 180°F, 0.65 gravity.",
    "⚙️ List Tools": "What technical calculations and reservoir engineering tools can you perform?"
}

# -----------------
# Chat Loop (Simplified for UI)
# -----------------
def _chat_with_agent(user_input):
    client = OpenAI(
        api_key=API_KEY, 
        base_url=BASE_URL,
    )
    full_prompt = user_input
    if user_context:
        full_prompt += f"\n\n[USER CONTEXT DATA]:\n{user_context}"
        
    st.session_state.messages.append({"role": "user", "content": full_prompt})
    
    with tab_chat:
        with st.chat_message("user", avatar="👤"):
            st.markdown(full_prompt)

        with st.chat_message("assistant", avatar="🤖"):
            message_placeholder = st.empty()
            message_placeholder.markdown("🧠 Thinking...")
            
            # Format messages for OpenAI
            messages_for_api = []
            for m in st.session_state.messages:
                api_msg = {"role": m["role"]}
                if "content" in m: api_msg["content"] = m["content"]
                if "tool_calls" in m: api_msg["tool_calls"] = m["tool_calls"]
                if "tool_call_id" in m: api_msg["tool_call_id"] = m["tool_call_id"]
                if "name" in m: api_msg["name"] = m["name"]
                messages_for_api.append(api_msg)

            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages_for_api,
                    tools=openai_tools,
                    tool_choice="auto"
                )
                response_message = response.choices[0].message
                msg_dict = {"role": response_message.role, "content": response_message.content}
                if response_message.tool_calls:
                    msg_dict["tool_calls"] = []
                    for tc in response_message.tool_calls:
                        msg_dict["tool_calls"].append({
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                        })
                st.session_state.messages.append(msg_dict)
                
                # Handle recursive tool calls until model stops
                while response_message.tool_calls:
                    for tool_call in response_message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)
                        message_placeholder.markdown(f"⚙️ Executing: `{func_name}`")
                        
                        try:
                            tool_result = run_sync(call_mcp_tool, func_name, func_args)
                            res_text = "\n".join([c.text for c in tool_result.content if getattr(c, 'type', '') == 'text'])
                            if not res_text:
                                res_text = str([c.model_dump() for c in tool_result.content])
                        except Exception as e:
                            res_text = f"Error executing tool {func_name}: {e}"
                            
                        st.session_state.messages.append({
                            "role": "tool", "tool_call_id": tool_call.id, "name": func_name, "content": res_text
                        })
                        
                    messages_for_api = []
                    for m in st.session_state.messages:
                        api_msg = {"role": m["role"]}
                        if "content" in m: api_msg["content"] = m["content"]
                        if "tool_calls" in m: api_msg["tool_calls"] = m["tool_calls"]
                        if "tool_call_id" in m: api_msg["tool_call_id"] = m["tool_call_id"]
                        if "name" in m: api_msg["name"] = m["name"]
                        messages_for_api.append(api_msg)

                    message_placeholder.markdown("🧠 Analyzing results...")
                    response = client.chat.completions.create(
                        model=MODEL_NAME, messages=messages_for_api, tools=openai_tools, tool_choice="auto"
                    )
                    response_message = response.choices[0].message
                    msg_dict = {"role": response_message.role, "content": response_message.content}
                    if response_message.tool_calls:
                        msg_dict["tool_calls"] = []
                        for tc in response_message.tool_calls:
                            msg_dict["tool_calls"].append({
                                "id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                            })
                    st.session_state.messages.append(msg_dict)
                
                # Final rendering logic
                final_text = response_message.content or ""
                json_start = final_text.rfind("```json")
                json_end = final_text.rfind("```", json_start + 7)
                
                if json_start != -1 and json_end != -1:
                    json_str = final_text[json_start+7 : json_end].strip()
                    display_text = final_text[:json_start].strip()
                    message_placeholder.markdown(display_text)
                    
                    try:
                        plot_data = json.loads(json_str)
                        if plot_data.get("plot_type") == "table":
                            st.dataframe(pd.DataFrame(plot_data.get("data", {})))
                        elif plot_type := plot_data.get("plot_type") == "line":
                            fig = go.Figure()
                            for s_name, s_data in plot_data.get("series", {}).items():
                                fig.add_trace(go.Scatter(x=s_data["x"], y=s_data["y"], mode='lines+markers', name=s_name))
                            fig.update_layout(xaxis_title=plot_data.get("x_label", "X"), yaxis_title=plot_data.get("y_label", "Y"), title=plot_data.get("title", "Simulation"))
                            st.plotly_chart(fig, use_container_width=True)
                    except:
                        st.code(json_str)
                else:
                    message_placeholder.markdown(final_text)
                
                # Feedback widget
                st.feedback("thumbs", key=f"fb_{len(st.session_state.messages)}")

            except Exception as e:
                st.error(f"API Error: {e}")

# Render Premium Custom Header at the top of the app
tool_count = len(st.session_state.openai_tools) if "openai_tools" in st.session_state else 0
_PREMIUM_HEADER(data={"model": MODEL_NAME, "toolCount": tool_count}, key="app_header")

# -----------------
# UI Tabs
# -----------------
tab_chat, tab_guide = st.tabs(["💬 AI Agent", "📖 User Guide"])

with tab_chat:
    # Onboarding Pills (Only if chat is basically empty - system prompt only)
    if len(st.session_state.messages) <= 1:
        st.markdown("### 👋 How can I assist today?")
        selected_suggestion = st.pills(
            "Quick Tasks:", 
            list(SUGGESTIONS.keys()), 
            label_visibility="collapsed"
        )
        if selected_suggestion:
            _chat_with_agent(SUGGESTIONS[selected_suggestion])
            st.rerun()

    # Render previous messages
    for idx, msg in enumerate(st.session_state.messages):
        if msg["role"] == "system": 
            continue
        if msg["role"] == "tool":
            continue 
            
        display_content = msg.get("content", "")
        if isinstance(msg.get("tool_calls"), list):
            func_calls = [tc["function"]["name"] for tc in msg["tool_calls"]]
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"*(Called: `{', '.join(func_calls)}`)*")
            continue

        if display_content and isinstance(display_content, str):
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
                st.markdown(display_content)

    st.divider()
    # Bottom Controls
    col_clear, _ = st.columns([1, 4])
    with col_clear:
        if st.button("🗑️ Clear History"):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.rerun()

    if prompt := st.chat_input("Ask a technical question..."):
        _chat_with_agent(prompt)

with tab_guide:
    st.header("📖 pyResToolbox Technical Guide")
    st.markdown("Advanced Reservoir Engineering & Production Optimization Toolkit.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("🧪 Oil PVT Analysis", expanded=True):
            st.markdown("""
            - **Bubble Point Pressure**: Standing, Valko-McCain, Velarde.
            - **Properties**: Solution GOR, FVF, viscosity, density, compressibility.
            - *Example*: "Calculate oil bubble point (Standing) for 200°F, 0.7 Gas Gravity, API 35."
            - *Example*: "Generate PVTO table for pressure 500 to 5000 psia."
            """)
            
        with st.expander("☁️ Gas PVT Analysis"):
            st.markdown("""
            - **Z-Factor**: DAK, Hall-Yarborough, WYW, BUR/Peng-Robinson.
            - **Hydrogen/CO2**: BUR method (SPE-229932-MS).
            - *Example*: "Find gas Z-factor (DAK) at 4000 psia, 180°F, 0.65 gravity."
            - *Example*: "Calculate gas PVT for a mixture with 20% H2 and 5% CO2 at 3000 psia."
            """)

        with st.expander("📈 Well Performance & IPR"):
            st.markdown("""
            - **Production Rates**: Radial and linear flow for oil and gas.
            - **IPR Curves**: Vogel IPR for P < Pb, horizontal wells.
            - *Example*: "Generate Vogel IPR curve for Pi=4000, Pb=3500, J=1.5."
            - *Example*: "Calculate oil rate for radial flow with k=50md, h=30ft, skin=2."
            """)

        with st.expander("💻 Reservoir Simulation Support"):
            st.markdown("""
            - **Rel Perm**: Corey, LET, Jerauld models.
            - **ECLIPSE**: PVDO/PVDG/PVTO, VFPPROD/VFPINJ, AQUTAB.
            - *Example*: "Generate Corey rel perm table for Swc=0.2, Sor=0.3, no=2, nw=3."
            - *Example*: "Create VFPPROD table for a well with 3.5 inch tubing and HB correlation."
            """)

        with st.expander("🎯 Nodal Analysis & VLP"):
            st.markdown("""
            - **VLP**: WG, HB, Gray, BB correlations.
            - **Workflow**: Operating point and outflow curves.
            - *Example*: "Perform Nodal Analysis for Pi=5000, J=2, and VLP using Beggs-Brill."
            - *Example*: "Generate VLP curve for a horizontal well with 5000ft lateral."
            """)

    with col2:
        with st.expander("📉 Decline Curve Analysis (DCA)", expanded=True):
            st.markdown("""
            - **Arps Models**: Exponential, hyperbolic, harmonic.
            - **Forecasting**: Rate, cumulative production, and EUR.
            - *Example*: "Forecast Arps decline for Qi=1000, Di=0.5, b=0.4 for 10 years."
            - *Example*: "Estimate EUR using Duong decline for a shale gas well."
            """)
            
        with st.expander("⚖️ Material Balance"):
            st.markdown("""
            - **Oil & Gas**: Havlena-Odeh OOIP, P/Z Gas MB.
            - *Example*: "Calculate OOIP using Havlena-Odeh for we=0 and Np=500,000 stb."
            - *Example*: "Plot P/Z vs Gp and find OGIP for a gas reservoir."
            """)

        with st.expander("⚒️ Geomechanics (27 tools)"):
            st.markdown("""
            - **Stresses & Stability**: Eaton pore pressure, fracture gradient, breakout.
            - *Example*: "Estimate pore pressure (Eaton) at 12000ft with normal gradient=0.465."
            - *Example*: "Calculate safe mud weight window at 8000ft for a vertical well."
            """)

        with st.expander("🌊 Brine Properties"):
            st.markdown("""
            - **Brine VLE**: Soreide-Whitson and IAPWS-IF97.
            - *Example*: "Calculate brine density at 4000 psia, 150°F, Salinity 50,000 ppm."
            - *Example*: "Find CO2 solubility in brine at 3000 psia and 200°F."
            """)

        with st.expander("🚀 Advanced Calculations"):
            st.markdown("""
            - **Heterogeneity**: Lorenz coefficient, Dykstra-Parsons.
            - **Analysis**: Tornado plots and sensitivity sweeps.
            - *Example*: "Analyze reservoir heterogeneity with Lorenz coefficient for 5 layers."
            - *Example*: "Run sensitivity of Pi on IPR from 3000 to 6000 psia."
            """)


