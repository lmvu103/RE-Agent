import numpy as np

def calculate_bg(pressure, temp_f, z_factor=0.9):
    """
    Bg = 0.02827 * Z * (T_Rankine) / P_psi
    Returns rb/scf
    """
    temp_r = temp_f + 459.67
    return 0.02827 * z_factor * temp_r / pressure if pressure > 0 else 0

def calculate_gas_properties(gor, api, sg_gas, pressure, temp_f, water_cut, liquid_rate):
    """
    Returns dictionary with GVF, Turpin, and recommendations.
    """
    # 1. Solution GOR (Rs) - Lasater or Standing usually. Simplified linear here:
    rs = min(gor, 0.4 * pressure) # Mock assumption
    
    # 2. Free GOR
    free_gor = max(0, gor - rs)
    
    # 3. FVF
    bg = calculate_bg(pressure, temp_f)
    bo = 1.1 + 0.00005 * (rs + (temp_f-60))
    bw = 1.02
    
    # 4. Volumes at Intake
    # liquid_rate is surface flow.
    # q_oil_surf = liquid_rate * (1 - wc)
    wc = water_cut / 100.0
    q_oil_surf = liquid_rate * (1 - wc)
    q_w_surf = liquid_rate * wc
    
    q_oil_bh = q_oil_surf * bo
    q_w_bh = q_w_surf * bw
    q_gas_bh = q_oil_surf * free_gor * bg
    
    total_liq_bh = q_oil_bh + q_w_bh
    total_fluid_bh = total_liq_bh + q_gas_bh
    
    # GVF
    gvf = q_gas_bh / total_fluid_bh if total_fluid_bh > 0 else 0
    
    # Turpin
    # Turpin = (Vg / Vl) * (P_intake) ?? No.
    # Turpin Phi = Vg/Vl
    # Turpin Parameter = Phi / P * factor? 
    # Usually: Turpin = 2000 * (Vg_acfs / Vl_acfs) / P_psi
    # Vg/Vl is Ratio.
    phi = q_gas_bh / total_liq_bh if total_liq_bh > 0 else 0
    turpin = (2000 * phi / pressure) if pressure > 1 else 0
    
    recommendation = "Standard Intake"
    if gvf > 0.10: 
        if turpin > 1.0: # Turpin > 1 implies simple pattern
             recommendation = "Gas Separator Recommended"
        else:
             recommendation = "Gas Handler (AGH) limit"
             
    if gvf > 0.30:
        recommendation = "Separator + AGH Required"
        
    return {
        "gvf": gvf,
        "turpin": turpin,
        "recommendation": recommendation,
        "total_fluid_bh_bpd": total_fluid_bh,
        "free_gas_pct": gvf * 100
    }

def calculate_tdh(tvd, whp, pip, sg_mix):
    """
    TDH (ft)
    """
    whp_head = whp / (0.433 * sg_mix) if sg_mix > 0 else 0
    pip_head = pip / (0.433 * sg_mix) if sg_mix > 0 else 0
    friction = (tvd / 1000) * 20 # 20ft/1000ft loss mock
    
    tdh = tvd + whp_head + friction - pip_head
    return max(0, tdh)

def calculate_stages(tdh, head_per_stage):
    if head_per_stage <= 0: return 0
    return int(np.ceil(tdh / head_per_stage))

def calculate_hp_required(stages, hp_per_stage, sg_mix):
    return stages * hp_per_stage * sg_mix

def check_integrity(shut_in_head_ft, fluid_grad, pump_tvd, casing_burst):
    """
    Check if max pressure exceeds burst rating.
    """
    pd_max = (shut_in_head_ft * fluid_grad) + (pump_tvd * fluid_grad)
    return {
        "max_pressure": pd_max,
        "safe": pd_max < casing_burst
    }

def calculate_velocity(casing_id, motor_od, rate_bpd):
    """
    Returns velocity in ft/s
    """
    if casing_id <= motor_od: return 999.0
    
    # Annulus A (sq in)
    area_sq_in = (np.pi / 4) * (casing_id**2 - motor_od**2)
    area_sq_ft = area_sq_in / 144.0
    
    # Q in ft3/s
    q_cfs = rate_bpd * 5.615 / 86400
    
    return q_cfs / area_sq_ft if area_sq_ft > 0 else 0

def calculate_electrical(cable_ohms, amps, length_ft, motor_volts):
    """
    Returns voltage drop, surface voltage, surface KVA.
    """
    # Voltage Drop = 1.732 * I * R
    r_total = (cable_ohms * length_ft / 1000)
    v_drop = 1.732 * amps * r_total
    
    surf_volts = motor_volts + v_drop
    
    # KVA = 1.732 * V_surf * I / 1000
    kva = 1.732 * surf_volts * amps / 1000.0
    
    return {
        "v_drop": v_drop,
        "surf_voltage": surf_volts,
        "kva": kva
    }
