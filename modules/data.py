import pandas as pd

def get_pump_catalog():
    data = {
        "Model": [
            "RCX1000", "DN1300", "D1150", "D3000", "S4000", "G6200", # SLB
            "GN2500", "J2000", "F350-B", "P8" , "G125", "S200",     # BKR
            "NV1500", "NV2000", "E2500", "E4500"                    # NVM
        ],
        "Manufacturer": [
            "SLB", "SLB", "SLB", "SLB", "SLB", "SLB",
            "BKR", "BKR", "BKR", "BKR", "BKR", "BKR",
            "NVM", "NVM", "NVM", "NVM"
        ],
        "Series": [
            "400", "400", "400", "538", "538", "538",
            "538", "538", "338", "338", "400", "400",
            "406", "406", "512", "512"
        ],
        "Min_Rate_BPD": [
            800, 1000, 900, 2200, 3100, 4500,
            2000, 1800, 250, 50, 80, 150,
            1100, 1500, 1800, 3200
        ],
        "Max_Rate_BPD": [
            1400, 1700, 1500, 3800, 5200, 7500,
            3200, 2600, 450, 120, 180, 280,
            1900, 2600, 3500, 5700
        ],
        "BEP_Rate_BPD": [
            1100, 1350, 1150, 3000, 4000, 6200,
            2700, 2200, 350, 80, 125, 200,
            1500, 2000, 2500, 4500
        ],
        "Head_Coeff_A": [
            25, 28, 22, 35, 40, 50,
            35, 30, 15, 8, 12, 18,
            28, 30, 38, 45
        ], 
        "Head_Coeff_B": [
            0.005, 0.004, 0.006, 0.003, 0.002, 0.001,
            0.003, 0.0035, 0.015, 0.04, 0.02, 0.012,
            0.0045, 0.0038, 0.0025, 0.0018
        ],
        "Head_Coeff_C": [
            -0.00001, -0.000008, -0.000012, -0.000005, -0.000003, -0.000001,
            -0.000005, -0.000006, -0.00005, -0.0002, -0.00008, -0.00004,
            -0.000009, -0.000007, -0.000004, -0.000002
        ],
        "HP_per_Stage_at_BEP": [
            0.4, 0.5, 0.35, 0.9, 1.2, 2.0,
            0.9, 0.75, 0.1, 0.02, 0.04, 0.06,
            0.45, 0.6, 0.8, 1.5
        ] 
    }
    return pd.DataFrame(data)

def get_motor_catalog():
    data = {
        "Series": ["456", "456", "562", "562"],
        "HP_Rating": [50, 60, 100, 150],
        "Voltage_Rating": [460, 850, 1000, 2200],
        "Amps_Rating": [65, 45, 60, 42],
        "Efficiency": [0.85, 0.86, 0.88, 0.89],
        "PowerFactor": [0.82, 0.83, 0.85, 0.86]
    }
    return pd.DataFrame(data)

def get_protector_catalog():
    data = {
        "Series": ["400", "538"],
        "Max_Temp_F": [300, 350],
        "Type": ["Standard", "High Temp"]
    }
    return pd.DataFrame(data)

def get_cable_catalog():
    data = {
        "Size": ["#4", "#2", "#1", "1/0"],
        "Ohms_per_1000ft": [0.25, 0.16, 0.13, 0.10],
        "Max_Amps": [95, 130, 150, 170]
    }
    return pd.DataFrame(data)

def get_well_history():
    data = {
        "Well": ["CACA-01", "CACA-01", "CACA-01"],
        "Start Date": ["2021-01-10", "2022-05-15", "2023-08-20"],
        "Failure Mode": ["Electrical", "Mechanical", "Running"],
        "PSD": [7000, 7200, 7500],
        "Vendor": ["SLB", "BKR", "SLB"],
        "Pump Spec": ["RCX1000", "GN2500", "RCX1000"],
        "RUN": [1, 2, 3]
    }
    return pd.DataFrame(data)

def get_failure_database():
    data = {
        "Well": ["CACA-02", "CACA-05", "CACA-01"],
        "Year": [2021, 2022, 2021],
        "Manufacture": ["SLB", "PWL", "SLB"],
        "Area": ["Field A", "Field A", "Field A"],
        "Failure Item": ["Cable", "Shaft", "Motor"],
        "Failure Item Specific": ["Short Circuit", "Broken", "Burned"],
        "General Failure": ["Electrical", "Mechanical", "Electrical"]
    }
    return pd.DataFrame(data)
