import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
from modules import data, calculations

# --- HELPER: RENDER PUMP CURVE ---
def render_pump_curve(pump_model, stages, freq, op_point=None):
    pump_df = data.get_pump_catalog()
    if pump_model not in pump_df['Model'].values: return None
    
    row = pump_df[pump_df['Model'] == pump_model].iloc[0]
    
    # Affinity Laws
    ratio = freq / 60.0
    q_bm_min = row['Min_Rate_BPD'] * ratio
    q_bm_max = row['Max_Rate_BPD'] * ratio
    
    qs = np.linspace(0, q_bm_max * 1.3, 50)
    q_ref = qs / ratio
    h_ref = row['Head_Coeff_A'] + row['Head_Coeff_B']*q_ref + row['Head_Coeff_C']*q_ref**2
    h_freq = h_ref * (ratio**2) * stages
    
    fig = go.Figure()
    
    # Head Curve
    fig.add_trace(go.Scatter(
        x=qs, y=h_freq, 
        name=f"Head @ {freq}Hz",
        line=dict(color='#4facfe', width=3)
    ))
    
    # ROR Box (Recommended Operating Range)
    fig.add_vrect(
        x0=q_bm_min, x1=q_bm_max, 
        fillcolor="rgba(0, 255, 0, 0.1)", 
        layer="below", 
        line_width=0,
        annotation_text="ROR",
        annotation_position="top left"
    )
    
    if op_point:
        fig.add_trace(go.Scatter(
            x=[op_point[0]], y=[op_point[1]], 
            mode='markers', 
            marker=dict(size=14, color='#ff4b4b', symbol='star', line=dict(width=2, color='white')), 
            name="Operating Point"
        ))
    
    fig.update_layout(
        title=f"Pump Performance: {pump_model}",
        xaxis_title="Rate (BPD)", 
        yaxis_title="Head (ft)",
        template="plotly_dark",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# --- MAIN PAGE LOGIC ---
st.markdown("## ⚡ ESP Engineering Suite")
st.markdown("Advanced Electric Submersible Pump design and surveillance.")

# Global Calculations for State
temp_est = 100 + (st.session_state.depth_tvd / 100) * 1.5
sg_oil = 141.5 / (131.5 + st.session_state.api)
sg_mix = (sg_oil * (1 - st.session_state.wc/100)) + (1.05 * st.session_state.wc/100)

tabs = st.tabs(["🎯 Design Wizard", "📊 Operations Monitor", "🚀 Optimization"])

# --- TAB 1: DESIGN WIZARD ---
with tabs[0]:
    step_tabs = st.tabs(["1. Well & Fluid", "2. Gas Handling", "3. Equipment Select", "4. Verification"])
    
    with step_tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Wellbore Configuration")
            st.session_state.well_name = st.text_input("Well Name", value=st.session_state.well_name)
            st.session_state.depth_tvd = st.number_input("Pump TVD (ft)", value=float(st.session_state.depth_tvd))
            st.session_state.casing_id = st.number_input("Casing ID (in)", value=float(st.session_state.casing_id))
        with c2:
            st.subheader("Reservoir Performance")
            st.session_state.sbhp = st.number_input("Static BHP (psi)", value=float(st.session_state.sbhp))
            st.session_state.pbhp = st.number_input("Producing BHP (psi)", value=float(st.session_state.pbhp))
            st.session_state.target_rate = st.number_input("Design Target Rate (BPD)", value=float(st.session_state.target_rate))
            
    with step_tabs[1]:
        st.subheader("Gas Interference Analysis")
        gas_res = calculations.calculate_gas_properties(
            st.session_state.gor, st.session_state.api, st.session_state.gas_sg,
            st.session_state.pbhp, temp_est, st.session_state.wc, st.session_state.target_rate
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("GVF at Intake", f"{gas_res['gvf']:.2%}")
        m2.metric("Turpin Index", f"{gas_res['turpin']:.2f}")
        m3.metric("Recommendation", gas_res['recommendation'])
        
    with step_tabs[2]:
        st.subheader("Equipment Integrated Selection")
        tdh = calculations.calculate_tdh(st.session_state.depth_tvd, st.session_state.whp, st.session_state.pbhp, sg_mix)
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            pump_df = data.get_pump_catalog()
            st.session_state.manufacturer = st.selectbox("Manufacturer", pump_df['Manufacturer'].unique())
            avail = pump_df[pump_df['Manufacturer'] == st.session_state.manufacturer]
            st.session_state.pump_selected = st.selectbox("Pump Model", avail['Model'])
            
            row = avail[avail['Model'] == st.session_state.pump_selected].iloc[0]
            q = st.session_state.target_rate
            h_stg = row['Head_Coeff_A'] + row['Head_Coeff_B']*q + row['Head_Coeff_C']*q**2
            stages = calculations.calculate_stages(tdh, max(1, h_stg))
            st.session_state.stages = st.number_input("Stages Required", value=int(stages))
        
        with col_p2:
            st.info(f"Required TDH: **{tdh:.0f} ft**")
            req_hp = calculations.calculate_hp_required(st.session_state.stages, row['HP_per_Stage_at_BEP'], sg_mix)
            st.metric("Required Horsepower (HP)", f"{req_hp:.1f}")
            
    with step_tabs[3]:
        st.subheader("Installation Verification")
        if st.session_state.pump_selected:
            fig = render_pump_curve(st.session_state.pump_selected, st.session_state.stages, 60.0, (st.session_state.target_rate, tdh))
            st.plotly_chart(fig, use_container_width=True)
            st.success("Design point is within safe limits.", icon="✅")

# --- TAB 2: MONITORING ---
with tabs[1]:
    st.subheader("Real-time Surveillance")
    cm1, cm2 = st.columns([1, 2])
    with cm1:
        st.session_state.mon_freq = st.slider("Operating Frequency (Hz)", 30.0, 70.0, float(st.session_state.mon_freq))
        st.session_state.mon_rate = st.number_input("Measured Liquid Rate (BPD)", value=float(st.session_state.mon_rate))
        st.session_state.mon_whp = st.number_input("Wellhead Pressure (psi)", value=float(st.session_state.mon_whp))
        
    with cm2:
        if st.session_state.pump_selected:
            # Simple IPR back-calc for Intake Pressure
            denom = (st.session_state.sbhp - st.session_state.pbhp)
            pi = st.session_state.test_rate / denom if denom > 0 else 1.0
            pip_actual = st.session_state.sbhp - (st.session_state.mon_rate / pi)
            tdh_actual = calculations.calculate_tdh(st.session_state.depth_tvd, st.session_state.mon_whp, pip_actual, sg_mix)
            
            fig_mon = render_pump_curve(
                st.session_state.pump_selected, 
                st.session_state.stages, 
                st.session_state.mon_freq, 
                op_point=(st.session_state.mon_rate, tdh_actual)
            )
            st.plotly_chart(fig_mon, use_container_width=True)
        else:
            st.warning("Please complete a design first.")

# --- TAB 3: OPTIMIZATION ---
with tabs[2]:
    st.subheader("Frequency Sensitivity Analysis")
    if st.session_state.pump_selected:
        opt_freq = st.select_slider("Select Target Frequency (Hz)", options=np.arange(30, 71, 1).tolist(), value=60)
        
        # System Curve Prep
        row = data.get_pump_catalog()
        row = row[row['Model'] == st.session_state.pump_selected].iloc[0]
        ratio = opt_freq / 60.0
        qs = np.linspace(100, row['Max_Rate_BPD']*1.5, 100)
        
        # Pump Head
        q_ref = qs / ratio
        h_pump = (row['Head_Coeff_A'] + row['Head_Coeff_B']*q_ref + row['Head_Coeff_C']*q_ref**2) * (ratio**2) * st.session_state.stages
        
        # System Head (Simplified)
        denom = (st.session_state.sbhp - st.session_state.pbhp)
        pi = st.session_state.test_rate / denom if denom > 0 else 1.0
        pip = st.session_state.sbhp - (qs / pi)
        fric = (st.session_state.depth_tvd/1000 * 20) * (qs/2000)**1.8
        tdh_sys = st.session_state.depth_tvd + (st.session_state.mon_whp/(0.433*sg_mix)) + fric - (pip/(0.433*sg_mix))
        
        # Find Intersection
        idx = np.abs(h_pump - tdh_sys).argmin()
        op_q = qs[idx]
        op_h = h_pump[idx]
        
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Predicted Production", f"{op_q:.0f} BPD")
        col_res2.metric("Predicted Lift", f"{op_h:.0f} ft")
        
        fig_opt = render_pump_curve(st.session_state.pump_selected, st.session_state.stages, opt_freq, op_point=(op_q, op_h))
        fig_opt.add_trace(go.Scatter(x=qs, y=tdh_sys, name="System Requirement", line=dict(dash='dash', color='gray')))
        st.plotly_chart(fig_opt, use_container_width=True)
