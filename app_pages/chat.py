import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from openai import OpenAI
from mcp_utils import call_mcp_tool, run_sync

def parse_and_render_assistant_content(content, idx_suffix=""):
    """Parses content for JSON blocks and renders markdown + charts/tables."""
    if "```json" in content:
        parts = content.split("```json")
        st.markdown(parts[0].strip())
        
        for i, part in enumerate(parts[1:]):
            try:
                json_str = part.split("```")[0].strip()
                data = json.loads(json_str)
                
                if data.get("plot_type") == "table":
                    df = pd.DataFrame(data.get("data", {}))
                    st.dataframe(df, use_container_width=True)
                    st.download_button("📥 Download CSV", df.to_csv(index=False), f"data_{idx_suffix}_{i}.csv", key=f"dl_{idx_suffix}_{i}")
                elif data.get("plot_type") == "line":
                    fig = go.Figure()
                    for series_name, series_data in data.get("series", {}).items():
                        fig.add_trace(go.Scatter(x=series_data["x"], y=series_data["y"], name=series_name, mode='lines+markers'))
                    fig.update_layout(
                        title=data.get("title", ""),
                        xaxis_title=data.get("x_label", ""),
                        yaxis_title=data.get("y_label", ""),
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Show remaining text after JSON block in this part
                remaining = part.split("```", 1)
                if len(remaining) > 1 and remaining[1].strip():
                    st.markdown(remaining[1].strip())
            except Exception as e:
                st.code(f"Error parsing JSON block: {e}\n{part}")
    else:
        st.markdown(content)

def handle_chat():
    # Welcome Message
    if len(st.session_state.messages) <= 1:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown("""
            **Welcome to PERE Agent Console!** 🚀
            
            I am your advanced Petroleum Engineering assistant. I can help you with:
            - **PVT Properties**: Saturation pressure, FVF, viscosity, etc.
            - **Well Performance**: IPR, VLP, and Nodal analysis.
            - **Simulation support**: Generating tables for Eclipse/Petrel.
            - **Geomechanics**: Stress and pore pressure analysis.
            
            How can I assist your engineering work today?
            """)
    
    # Render existing messages
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "system":
            continue
        
        if msg["role"] == "tool":
            # Optional: show tool output in an expander or skip
            # with st.expander(f"🛠️ Tool: {msg['name']}", expanded=False):
            #     st.code(msg["content"])
            continue

        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            if msg["role"] == "assistant":
                if msg.get("tool_calls"):
                    tool_names = [tc["function"]["name"] for tc in msg["tool_calls"]]
                    st.caption(f"🛠️ Used tools: {', '.join(tool_names)}")
                if msg.get("content"):
                    parse_and_render_assistant_content(msg["content"], f"msg_{i}")
            else:
                st.markdown(msg["content"])

    # Chat Input
    prompt = st.chat_input("Ask PERE Agent... (e.g., Calculate bubble point for 1500 psia, 200 F)")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        # Agent Logic
        with st.chat_message("assistant", avatar="🤖"):
            with st.status("🧠 Processing engineering query...", expanded=True) as status:
                try:
                    # Dynamic Client Config based on Provider
                    base_urls = {
                        "Gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
                        "OpenAI": "https://api.openai.com/v1",
                        "OpenRouter": "https://openrouter.ai/api/v1",
                        "Groq": "https://api.groq.com/openai/v1"
                    }
                    
                    p = st.session_state.provider
                    active_key = st.session_state.get(f"{p.lower()}_api_key")
                    active_model = st.session_state.get(f"{p.lower()}_model")
                    
                    client = OpenAI(api_key=active_key, base_url=base_urls.get(p))
                    
                    while True:
                        # Prepare messages for API (Gemini/OpenAI format)
                        api_msgs = []
                        for m in st.session_state.messages:
                            clean_m = {"role": m["role"], "content": m.get("content") or ""}
                            if m.get("tool_calls"): clean_m["tool_calls"] = m["tool_calls"]
                            if m.get("tool_call_id"): clean_m["tool_call_id"] = m["tool_call_id"]
                            if m.get("name"): clean_m["name"] = m["name"]
                            api_msgs.append(clean_m)

                        # Robust Parameter Passing for different providers
                        client_kwargs = {
                            "model": active_model,
                            "messages": api_msgs,
                        }
                        
                        if st.session_state.openai_tools:
                            client_kwargs["tools"] = st.session_state.openai_tools
                            client_kwargs["tool_choice"] = "auto"
                        
                        if p == "OpenRouter":
                            client_kwargs["extra_headers"] = {
                                "HTTP-Referer": "https://per-agent.vercel.app", 
                                "X-Title": "PERE Agent"
                            }

                        response = client.chat.completions.create(**client_kwargs)
                        
                        resp_msg = response.choices[0].message
                        
                        if not resp_msg.tool_calls:
                            # Final answer
                            st.session_state.messages.append({"role": "assistant", "content": resp_msg.content})
                            parse_and_render_assistant_content(resp_msg.content, "new")
                            status.update(label="✅ Analysis Complete", state="complete", expanded=False)
                            break
                        
                        # Handle tool calls
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "tool_calls": [{"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in resp_msg.tool_calls]
                        })
                        
                        for tc in resp_msg.tool_calls:
                            status.update(label=f"⚙️ Executing: {tc.function.name}")
                            tool_args = json.loads(tc.function.arguments)
                            result = run_sync(call_mcp_tool, tc.function.name, tool_args)
                            
                            # Extract text from MCP response
                            tool_content = ""
                            if hasattr(result, "content"):
                                tool_content = "\n".join([c.text for c in result.content if hasattr(c, "text")])
                            else:
                                tool_content = str(result)
                                
                            st.session_state.messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": tc.function.name,
                                "content": tool_content
                            })
                            
                except Exception as e:
                    if "429" in str(e):
                        st.error("🚀 **Quota Exceeded (429)**: Limit reached for this model. Try switching providers/models below.")
                    else:
                        st.error(f"❌ Error: {e}")
                    status.update(label="⚠️ Error Occurred", state="error")

if __name__ == "__main__":
    # Settings Section (Multi-Provider)
    with st.expander("🛠️ Advanced Configuration", expanded=not any([st.session_state.gemini_api_key, st.session_state.openai_api_key, st.session_state.groq_api_key, st.session_state.openrouter_api_key])):
        st.session_state.provider = st.selectbox("🌐 Active Provider", ["Gemini", "OpenAI", "OpenRouter", "Groq"])
        p_low = st.session_state.provider.lower()
        
        # Key & Model inputs for selected provider
        key_var = f"{p_low}_api_key"
        model_var = f"{p_low}_model"
        
        c1, c2 = st.columns(2)
        with c1:
            st.text_input(f"🔑 {st.session_state.provider} API Key", key=key_var, type="password")
        with c2:
            st.text_input(f"🤖 Model ID", key=model_var)
            
    # Check if active key is properly loaded
    p_low = st.session_state.provider.lower()
    active_key = st.session_state.get(f"{p_low}_api_key")
    
    if active_key:
        handle_chat()
    else:
        st.warning(f"❌ **{st.session_state.provider} Key Missing**: Please enter your API Key in the settings panel above to unlock the agent.")
