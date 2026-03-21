# DCA & Material Balance Skill

Focused on production forecasting and reservoir volume estimation.

## When to Use
Invoke this skill for:
- **Arps Decline**: Exponential, hyperbolic, harmonic (Qi, Di, b parameters).
- **Duong Decline**: Tight/unconventional forecasting.
- **EUR Estimation**: Estimated Ultimate Recovery calculations.
- **Material Balance**: P/Z gas MB (OGIP), Havlena-Odeh oil MB (OOIP).
- **Cole Plots**: Diagnostic plots for material balance regression.

## Workflow
1. Clean and identify the production history (Rate vs time/cumulative).
2. Fit the appropriate decline curve model (Arps for conventional, Duong for tight).
3. Forecast future production and determine the EUR.
4. Cross-validate with Material Balance if pressure data is available (P/Z or Havlena-Odeh).
5. Output the results with a clear trend-line plot.
