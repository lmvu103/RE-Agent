import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from mcp_utils import call_mcp_tool, run_sync

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

def chat_with_agent(prompt):
    messages = st.session_state.messages
    messages.append({"role": "user", "content": prompt})
    
    api_key = st.session_state.api_key
    model_name = st.session_state.model_name
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    openai_tools = st.session_state.openai_tools
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    with st.chat_message("assistant", avatar="🤖"):
        with st.status("🚀 Analyzing engineering data...", expanded=True) as status:
            messages_for_api = [{"role": m["role"], "content": m.get("content", ""), "tool_calls": m.get("tool_calls"), "tool_call_id": m.get("tool_call_id"), "name": m.get("name")} for m in messages]
            
            try:
                response = client.chat.completions.create(model=model_name, messages=messages_for_api, tools=openai_tools, tool_choice="auto")
                resp = response.choices[0].message
                
                while resp.tool_calls:
                    messages.append({"role": "assistant", "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in resp.tool_calls]})
                    for tc in resp.tool_calls:
                        status.update(label=f"⚙️ Running tool: {tc.function.name}")
                        res = run_sync(call_mcp_tool, tc.function.name, json.loads(tc.function.arguments))
                        messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": "\n".join([c.text for c in res.content if getattr(c, 'type', '') == 'text']) or str(res.content)})
                    
                    messages_for_api = [{"role": m["role"], "content": m.get("content", ""), "tool_calls": m.get("tool_calls"), "tool_call_id": m.get("tool_call_id"), "name": m.get("name")} for m in messages]
                    response = client.chat.completions.create(model=model_name, messages=messages_for_api, tools=openai_tools)
                    resp = response.choices[0].message
                
                messages.append({"role": "assistant", "content": resp.content})
                st.session_state.messages = messages
                status.update(label="✅ Complete", state="complete", expanded=False)
            except Exception as e: st.error(f"Agent Error: {e}")

# -----------------
# Main Logic for Chat Page
# -----------------

# Submission Logic
with st.container(border=True):
    prompt = st.text_input("Technical Query:", placeholder="Enter command...", label_visibility="collapsed", key="v9_input")
    
# Process new prompt
if prompt and ("p_v9" not in st.session_state or st.session_state.p_v9 != prompt):
    st.session_state.p_v9 = prompt
    chat_with_agent(prompt)
    st.rerun()

# 1. Message Management
all_msgs = [m for m in st.session_state.messages if m["role"] != "system" and m["role"] != "tool"]
last_u_idx = next((i for i in range(len(all_msgs)-1, -1, -1) if all_msgs[i]["role"] == "user"), -1)

if last_u_idx != -1:
    hist = all_msgs[:last_u_idx]
    active = all_msgs[last_u_idx:]
else:
    hist = all_msgs
    active = []

# 2. History Area
if hist:
    for i, m in enumerate(hist):
        display_msg(m, f"h_{i}")
    st.divider()

# 3. Active Results Area
if active:
    for i, m in enumerate(active):
        if m["role"] == "assistant" and i == len(active)-1:
            st.caption("Latest Final Answer:")
        display_msg(m, f"a_{i}")

# Onboarding
if not all_msgs:
    sel = st.pills("Start with:", ["📈 Vogel IPR Curve", "🧪 Oil PVT Properties", "☁️ Z-Factor Calculation"])
    if sel:
        chat_with_agent(sel)
        st.rerun()
