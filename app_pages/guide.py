import streamlit as st

st.header("📖 Technical Guide")
st.markdown("Professional tools for Reservoir and Production Engineers.")
c1, c2 = st.columns(2)
with c1:
    with st.expander("🧪 PVT", expanded=True): 
        st.write("- Oil & Gas properties\n- S-W Brine model")
    with st.expander("📈 IPR"): 
        st.write("- Vogel & Radial flow\n- Horizontal wells")
with c2:
    with st.expander("📉 Decline Curve"): 
        st.write("- Arps and Duong models")
    with st.expander("⚒️ Geomechanics"): 
        st.write("- Pore pressure & Stress")
