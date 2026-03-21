# Simulation Support Skill

Focused on preparing fluid and rock-fluid data for reservoir simulators (ECLIPSE, Intersect).

## When to Use
Invoke this skill for:
- **Rel Perm Curves**: Corey, LET, Jerauld models (SWOF, SGOF, SGWFN).
- **Black Oil Tables**: PVDO, PVDG, PVTO for oil and gas components.
- **Water PVT**: PVTW generation with salinity corrections.
- **VFP Tables**: VFPPROD and VFPINJ lift curve tables.
- **Aquifer Functions**: Van Everdingen & Hurst (AQUTAB).

## Workflow
1. Define the pressure range and saturation steps for the tables.
2. Select the appropriate fluid model (Standing/DAK/McCain).
3. Generate the structured tabular data.
4. Export or format the output in a layout compatible with reservoir simulators.
5. Provide a visualization of the rel perm or PVT curves.
