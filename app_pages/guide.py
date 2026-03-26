import streamlit as st

st.markdown("## 📖 PERE Agent User Guide")
st.markdown("Master the features of your Petroleum Engineering Research & Engineering Agent.")

tabs = st.tabs([
    "🧪 PVT Analysis", 
    "📈 Well Performance", 
    "🛢️ Reservoir Simulation", 
    "📊 DCA & MBAL", 
    "⚒️ Geomechanics",
    "💧 Brine Props"
])

with tabs[0]:
    st.markdown("### Fluid Analysis (PVT)")
    st.info("Calculate black oil properties, gas compressibility, and saturation pressure.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Key Functions:**")
        st.markdown("- Bubble point pressure ($P_b$)\n- Oil/Gas Formulation Volume Factor ($B_o$, $B_g$)\n- Solution GOR ($R_s$)\n- Oil Viscosity ($\mu_o$)")
    with col2:
        st.write("**Example Questions:**")
        st.code("Calculate bubble point for 35 API oil, 0.8 gas gravity, at 180 F.")
        st.code("Find oil FVF and GOR for a 2500 psi reservoir at 200 F.")
        st.code("What is the Z-factor for gas with 0.7 gravity at 3000 psi and 150 F?")

with tabs[1]:
    st.markdown("### Well Performance (IPR/VLP)")
    st.info("Analyze inflow performance and nodal analysis.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Key Functions:**")
        st.markdown("- Vogel IPR curve\n- Standing's IPR\n- Productivity Index ($PI$)\n- AOP (Absolute Open Flow)")
    with col2:
        st.write("**Example Questions:**")
        st.code("Generate a Vogel IPR curve for a well with Pb=2000 psi, Pr=3000 psi, and q_max=500 bpd.")
        st.code("Calculate the PI for a reservoir with 50 md permeability and 20 ft thickness.")

with tabs[2]:
    st.markdown("### Reservoir Simulation Support")
    st.info("Generate tables for simulation software like Eclipse or Petrel.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Key Functions:**")
        st.markdown("- Black Oil Tables (PVTO/PVTG)\n- Relative Permeability (Corey/LET)\n- PVTW (Water properties)")
    with col2:
        st.write("**Example Questions:**")
        st.code("Create a PVTO table for 40 API oil from 500 to 5000 psi.")
        st.code("Generate Corey relative permeability curves with Sor=0.2 and Swr=0.25.")

with tabs[3]:
    st.markdown("### DCA & Material Balance")
    st.info("Forecast production and estimate Original Oil In Place.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Key Functions:**")
        st.markdown("- Arps Decline (Exponential, Hyperbolic)\n- Havlena-Odeh Material Balance\n- P/Z Gas Analysis")
    with col2:
        st.write("**Example Questions:**")
        st.code("Forecast production for 24 months using Arps hyperbolic decline with b=0.5, di=0.1, and qi=100.")
        st.code("Perform P/Z analysis for a gas reservoir with the following pressure-cum data...")

with tabs[4]:
    st.markdown("### Geomechanics")
    st.info("Assess stresses and safe mud weight windows.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Key Functions:**")
        st.markdown("- Vertical/Horizontal Stress\n- Eaton Pore Pressure\n- Mud Weight Window")
    with col2:
        st.write("**Example Questions:**")
        st.code("Calculate vertical stress at 12000 ft with 2.3 g/cm3 average density.")
        st.code("Estimate pore pressure using Eaton's method for a 10000 ft well.")

with tabs[5]:
    st.markdown("### Brine Properties")
    st.info("Accurate properties for formation water and completion fluids.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Key Functions:**")
        st.markdown("- Brine Density\n- Water Solubility\n- Salinity Correction")
    with col2:
        st.write("**Example Questions:**")
        st.code("Calculate brine density for 100,000 ppm salinity at 150 F and 2000 psi.")
        st.code("What is the water solubility in gas at 200 F and 5000 psi?")

st.divider()
st.caption("Tip: You can copy any example question and paste it into the Agent Console.")
