# PVT Property Skill

Focused on fluid property characterization and PVT data validation.

## When to Use
Invoke this skill for:
- **Bubble Point Pressure**: Standing, Valko-McCain, Velarde correlations.
- **Gas Z-Factor**: DAK, Hall-Yarborough, BUR/Peng-Robinson.
- **Hydrogen-Capable Mixes**: SPE-229932-MS method for H2/CO2 blends.
- **Oil/Gas Properties**: FVF, Solution GOR, Viscosity, Density, Compressibility.

## Workflow
1. Identify the input data: T (F), P (psia), SG (oil/gas), salinity.
2. Select the correct correlation if not specified (e.g., Standing for most cases).
3. Perform the calculation and validate with known benchmarks.
4. Explain the physical significance of the results (e.g., 'The high Rs indicates high gas solubility').
