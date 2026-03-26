import plotly.graph_objects as go
import numpy as np

def plot_combined_curves(pump_name, q_min, q_max, head_coeffs, stages, design_rate, tdh, design_hp):
    """
    Plot Pump Head Curve vs System Head Curve (Reference).
    """
    # Flow rates
    q = np.linspace(q_min * 0.5, q_max * 1.2, 100)
    
    # Pump Head (Head/stg * stages)
    h_stg = head_coeffs['A'] + head_coeffs['B']*q + head_coeffs['C']*q**2
    h_total = h_stg * stages
    
    fig = go.Figure()
    
    # Pump Curve
    fig.add_trace(go.Scatter(x=q, y=h_total, mode='lines', name=f'{pump_name} Performance', line=dict(color='blue')))
    
    # Operating Point
    fig.add_trace(go.Scatter(x=[design_rate], y=[tdh], mode='markers', name='Operating Point', 
                             marker=dict(color='red', size=12, symbol='star')))
    
    fig.update_layout(
        title=f"Pump Performance Curve: {pump_name} ({stages} stg)",
        xaxis_title="Flow Rate (BPD)",
        yaxis_title="Head (ft)",
        hovermode="x unified"
    )
    

def plot_ipr_curve(sbhp, pbhp, test_rate, mode='linear'):
    """
    Generate IPR Curve (Pwf vs Rate).
    mode: 'linear' or 'vogel'
    """
    fig = go.Figure()
    
    # Calculate AOFP
    # Linear: J = q / (Ps - Pwf) => q = J(Ps - Pwf) => At Pwf=0, q_max = J*Ps
    # Vogel: q/q_max = 1 - 0.2(Pwf/Ps) - 0.8(Pwf/Ps)^2
    
    if sbhp <= pbhp: # Invalid data check
        return fig
        
    if mode == 'linear':
        denom = (sbhp - pbhp)
        if denom == 0: denom = 0.001
        pi = test_rate / denom
        aofp = pi * sbhp
        
        # Points
        p_vals = np.linspace(0, sbhp, 50)
        q_vals = pi * (sbhp - p_vals)
        
    else: # Vogel
        # Calc q_max (AOFP) first
        # q_test / q_max = 1 - 0.2(p/p_s) - 0.8(p/p_s)^2
        ratio_p = pbhp / sbhp
        vogel_factor = 1.0 - 0.2*(ratio_p) - 0.8*(ratio_p**2)
        if vogel_factor == 0: vogel_factor = 0.001
        aofp = test_rate / vogel_factor
        
        p_vals = np.linspace(0, sbhp, 50)
        q_vals = aofp * (1.0 - 0.2*(p_vals/sbhp) - 0.8*((p_vals/sbhp)**2))
        pi = aofp / sbhp * 1.8 # Rough proxy for PI at Ps (derivative)
    
    fig.add_trace(go.Scatter(x=q_vals, y=p_vals, mode='lines', name='IPR', line=dict(color='blue')))
    
    # Test Point
    fig.add_trace(go.Scatter(x=[test_rate], y=[pbhp], mode='markers', name='Test Point', 
                             marker=dict(color='red', size=10)))
                             
    fig.update_layout(
        title="IPR Plot",
        xaxis_title="Rate (STB/d)",
        yaxis_title="Pwf (psia)",
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    
    return fig, pi
