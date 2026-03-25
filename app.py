import streamlit as st
import asyncio
import os
import sys
import threading
from concurrent.futures import Future
from streamlit.runtime.scriptrunner import add_script_run_ctx
from mcp import StdioServerParameters
from mcp_utils import get_all_tools, run_sync

# Path configuration
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_DIR = os.path.join(ROOT_DIR, "mcp_server")

SYSTEM_PROMPT = """You are an expert Petroleum Engineering AI Assistant (PERE Agents).
Use provided tools to perform reservoir engineering calculations.
Always provide a JSON block at the VERY END for tabular/chart data.
Table: {"plot_type": "table", "data": {"Col": []}}
Chart: {"plot_type": "line", "x_label": "X", "y_label": "Y", "series": {"S1": {"x": [], "y": []}}}
"""

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

# -----------------
# Global State Initialization
# -----------------
def init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    if "openai_tools" not in st.session_state:
        try:
            tools_list = run_sync(get_all_tools)
            st.session_state.openai_tools = [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}} for t in tools_list]
        except Exception as e:
            st.error(f"MCP Connection Error: {e}")
            st.stop()
            
    if "api_key" not in st.session_state:
        st.session_state.api_key = st.secrets.get("GEMINI_API_KEY", "")
        
    if "model_name" not in st.session_state:
        st.session_state.model_name = "gemini-2.0-flash"

init_state()

# -----------------
# Sidebar (Shared)
# -----------------
with st.sidebar:
    st.header("⚙️ Agent Settings")
    st.session_state.api_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")
    st.session_state.model_name = st.selectbox("Gemini Model", [
        "gemini-2.0-flash", "gemini-2.5-flash", "gemini-3-flash-preview", "gemini-flash-latest"
    ], index=["gemini-2.0-flash", "gemini-2.5-flash", "gemini-3-flash-preview", "gemini-flash-latest"].index(st.session_state.model_name))
    st.divider()
    with st.expander("💡 Helper Tools", expanded=False):
        st.markdown("- IPR Curves\n- PVT properties\n- Nodal Analysis\n- DCA Forecasting")

# -----------------
# Navigation
# -----------------
page = st.navigation([
    st.Page("app_pages/chat.py", title="AI Agent", icon="💬"),
    st.Page("app_pages/guide.py", title="User Guide", icon="📖"),
], position="sidebar")

# Shared Header
header_result = _PREMIUM_HEADER(data={"model": st.session_state.model_name, "toolCount": len(st.session_state.openai_tools)}, key="header")
if getattr(header_result, "reset", False):
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.rerun()

# Run the page
page.run()
