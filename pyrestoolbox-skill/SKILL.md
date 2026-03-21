# pyResToolbox Engineering Skill

This is a **routing skill** that directs you to specialized petroleum engineering calculations and simulations using the pyResToolbox MCP Server.

## When to Use
Invoke this skill when the user's request involves:
- **Fluid Analysis (PVT)**: Bubble point, GOR, FVF, viscosity, density, Z-factor.
- **Well Performance**: IPR curves, VLP curves, Nodal analysis, production rates.
- **Reservoir Simulation**: Black Oil tables, PVTW tables, rel perm curves (Corey/LET/Jerauld).
- **Decline Curve Analysis (DCA)**: Arps, Duong decline, cumulative forecasting.
- **Geomechanics**: Pore pressure, vertical/horizontal stress, mud weight window.
- **Brine Properties**: Solubility, density, salinity corrections (IAPWS-IF97).
- **Material Balance**: P/Z gas MB, Havlena-Odeh oil MB.

**Trigger phrases**: "PVT", "bubble point", "IPR curve", "Nodal analysis", "Z-factor", "Black Oil table", "rel perm", "decline curve", "DCA", "OOIP", "OGIP", "Eaton pore pressure", "mud weight", "Vogel", "Arps", "Standing", "Cole plot".

## Workflow
```
Step 1: Define Fluid Properties (PVT)
    ↓
Step 2: Calculate Inflow/Outflow Performance (IPR/VLP)
    ↓
Step 3: Analyze Production History or Simulation Tables
    ↓
Step 4: Generate Technical Report with Plotly Charts
```

## Professional Tips
- **Consistency**: Always use the same fluid model (e.g., Standing/DAK) for related calculations.
- **Plotting**: Always output JSON formatting for the Streamlit frontend to render Plotly charts.
- **Formatting**: Don't just give numbers; provide context (e.g., explain WHY the bubble point is important for the specific request).

## Skill Map
- [PVT Property Skill](skills/pvt/SKILL.md)
- [Well Performance Skill](skills/well_performance/SKILL.md)
- [Simulation Support Skill](skills/simulation/SKILL.md)
- [Geomechanics Skill](skills/geomechanics/SKILL.md)
- [DCA & Material Balance Skill](skills/analysis/SKILL.md)
