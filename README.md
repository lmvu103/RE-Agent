# 🛢️ RE-Agent: Professional Reservoir Engineering AI Assistant

**RE-Agent** is a state-of-the-art AI-powered platform for petroleum engineering tasks, built with **Streamlit** and powered by the **pyResToolbox** Model Context Protocol (MCP) server.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
[![Petroleum Engineering](https://img.shields.io/badge/Domain-Petroleum%20Engineering-darkblue)](https://github.com/lmvu103/RE-Agent)

## 🚀 Overview
RE-Agent provides a conversational interface for complex reservoir engineering calculations, diagnostics, and simulations. By combining the power of Large Language Models (LLMs) via **OpenRouter** with the technical precision of **pyResToolbox**, this agent can perform over 100+ specialized engineering functions.

## 🛠️ Key Capabilities

| Category | Features |
| :--- | :--- |
| **🧪 PVT Analysis** | Bubble point (Standing/Valko), Z-factor (DAK/BUR), H2-capable gas PVT (SPE-229932-MS). |
| **📈 Production** | Nodal Analysis, IPR (Vogel/Darcy), VLP curves (Hagedorn-Brown/Beggs-Brill). |
| **💻 Simulation** | ECLIPSE table generation (PVDO/PVDG/VFP), Rel Perm fitting (Corey/LET). |
| **📉 Analysis** | DCA (Arps/Duong), EUR forecasting, Material Balance (P/Z & Havlena-Odeh). |
| **⚒️ Geomechanics** | Pore pressure prediction, mud weight window, stress polygon, fault stability. |
| **🌊 Brine VLE** | CO2/CH4 solubility, IAPWS-IF97 density, salinity corrections. |

## 🧠 Digital Skills System
RE-Agent includes a **Professional Digital Skillset** located in `/pyrestoolbox-skill/`. These skills guide AI agents with technical workflows to ensure:
- **Consistency**: Using appropriate correlations for different fluid types.
- **Workflow-Driven**: Step-by-step logic from characterization to simulation.
- **Data Integrity**: Automated validation and unit conversions.

## 💻 Tech Stack
- **Frontend**: Streamlit (with Plotly visualizations)
- **Engine**: pyResToolbox (via MCP Server)
- **AI Backend**: OpenRouter (Google Gemini 2.0 Flash)
- **Deployment**: Optimized for Streamlit Cloud

## 📦 Installation & Setup

### Local Run
1. Clone the repository:
   ```bash
   git clone https://github.com/lmvu103/RE-Agent.git
   cd RE-Agent
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

### Streamlit Cloud Deployment
- Connect this repo to [Streamlit Cloud](https://share.streamlit.io/).
- Set your `OPENROUTER_API_KEY` in the **App Secrets** dashboard.

## 📜 License
This project is licensed under the GPL-3.0 License - see the LICENSE file for details.

---
*Developed with ❤️ for the Petroleum Engineering community by [lmvu103](https://github.com/lmvu103).*
