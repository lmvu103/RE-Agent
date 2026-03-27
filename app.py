import streamlit as st
import os
from mcp_utils import get_all_tools, run_sync

# --- 1. GLOBAL CONFIG ---
st.set_page_config(
    page_title="PERE Agent | AI Suite",
    page_icon="🤖",
    layout="wide",
)

# Load Premium CSS
CSS_PATH = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(CSS_PATH):
    with open(CSS_PATH) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- 2. GLOBAL STATE ---
def initialize_engine():
    # Multi-Provider Configuration
    if "provider" not in st.session_state:
        st.session_state.provider = "OpenRouter" # Default
    
    # SECURE PRACTICE: Using st.secrets. 
    # Add your keys to the Streamlit Cloud Dashboard (Settings > Secrets) for live deployment.
    providers_info = {
        "Gemini": {"key": "GEMINI_API_KEY", "model": "gemini-2.5-flash"},
        "OpenAI": {"key": "OPENAI_API_KEY", "model": "gpt-5.4"},
        "OpenRouter": {"key": "OPENROUTER_API_KEY", "model": "google/gemini-2.0-flash-001"},
        "Groq": {"key": "GROQ_API_KEY", "model": "llama-3.3-70b-versatile"},
    }
    
    for p, info in providers_info.items():
        key_name = f"{p.lower()}_api_key"
        model_name = f"{p.lower()}_model"
        
        # Priority 1: Use value from Secrets if not already set by user
        if key_name not in st.session_state or not st.session_state[key_name]:
            secret_val = st.secrets.get(info["key"], "")
            st.session_state[key_name] = secret_val
            
        # Priority 2: Use default model if not set
        if model_name not in st.session_state or not st.session_state[model_name]:
            st.session_state[model_name] = info["model"]

    # Current Active session aliases
    st.session_state.api_key = st.session_state.get(f"{st.session_state.provider.lower()}_api_key", "")
    st.session_state.model_name = st.session_state.get(f"{st.session_state.provider.lower()}_model", "")
    
    # AI Messages
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "system", 
            "content": "You are PERE Agent, an expert Petroleum Engineering AI. Use tools for calculations."
        }]
    
    # MCP Tools
    if "openai_tools" not in st.session_state:
        try:
            with st.spinner("Initializing AI Engine..."):
                tools = run_sync(get_all_tools)
                st.session_state.openai_tools = [
                    {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}} 
                    for t in tools
                ]
        except:
            st.session_state.openai_tools = []

initialize_engine()

# --- 3. SIDEBAR (NAVIGATION) ---
with st.sidebar:
    st.title("PERE AI")
    st.divider()
    if st.button("🗑️ Clear Live Console", use_container_width=True):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

# --- 4. NAVIGATION & HEADER ---
st.markdown(f"""
<div class="header-container">
    <div style="display: flex; align-items: center; gap: 15px;">
        <span style="font-size: 2.2rem;">🤖</span>
        <div>
            <div class="main-title">PERE AI Agent</div>
            <div class="sub-title">Research & Engineering Intelligence</div>
        </div>
    </div>
    <div class="status-area">
        <div class="status-chip">
            <div class="chip-label">Engine</div>
            <div class="chip-value">Active: {len(st.session_state.openai_tools)} Tools</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

pg = st.navigation({
    "Intelligent Agent": [
        st.Page("app_pages/chat.py", title="AI Console", icon="💬", default=True),
        st.Page("app_pages/guide.py", title="Skill Library", icon="📖"),
    ]
})

pg.run()
