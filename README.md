# 🧠 NEXORA  
Adaptive Regime Detection and Strategy Optimization Framework for Quantitative Trading  

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://github.com/tobollie2/NEXORA/actions/workflows/nexora-ci.yml/badge.svg)](https://github.com/tobollie2/NEXORA/actions/workflows/nexora-ci.yml)
[![Model Retraining](https://github.com/tobollie2/NEXORA/actions/workflows/nexora-train.yml/badge.svg)](https://github.com/tobollie2/NEXORA/actions/workflows/nexora-train.yml)
[![Last Commit](https://img.shields.io/github/last-commit/tobollie2/NEXORA.svg)](https://github.com/tobollie2/NEXORA/commits/main)


[![CI Status](https://github.com/tobollie2/NEXORA/actions/workflows/nexora-ci.yml/badge.svg)](https://github.com/tobollie2/NEXORA/actions/workflows/nexora-ci.yml)
[![Model Retraining](https://github.com/tobollie2/NEXORA/actions/workflows/nexora-train.yml/badge.svg)](https://github.com/tobollie2/NEXORA/actions/workflows/nexora-train.yml)

---

## 🔍 Overview  

**NEXORA** is an adaptive AI framework for **financial regime detection**, **strategy optimization**, and **portfolio risk management**.  
It blends econometric modeling, deep learning, and reinforcement learning to identify and adapt to changing market regimes in real time.  

The framework integrates:  
- 🧩 **LSTM-based regime detection**  
- 🧠 **Meta-learning for adaptive strategy selection**  
- 📉 **Dynamic risk control and Value-at-Risk monitoring**  
- 📊 **Comprehensive backtesting and reporting**  
- ⚙️ **Fully automated optimization and CI/CD integration**

---

## ⚙️ Architecture  

NEXORA/
│
├── ai/ # Core intelligence and learning modules
│ ├── meta_agent.py # Central AI orchestrator
│ ├── regime_forecaster.py
│ ├── reward_functions.py
│ └── models/ # LSTM, drift monitoring, and trainers
│
├── backtest/ # Simulation and performance evaluation
│ ├── backtest_runner.py
│ ├── performance_metrics.py
│ └── report_generator.py
│
├── optimization/ # Strategy and hyperparameter optimization
│ ├── optimizers/ # Bayesian, Genetic, Grid Search
│ └── optimization_runner.py
│
├── monitoring/ # Logging, dashboards, and system health
│ ├── live_dashboard.py
│ └── logging_utils.py
│
├── data/ # Ingestion, features, and Kraken data pipelines
│ ├── download_kraken_data.py
│ ├── feature_store.py
│ └── kraken_client.py
│
├── tools/ # Diagnostics and maintenance utilities
│
├── live/ # Live trading and execution layer
│
├── risk/ # Risk management logic
│
├── portfolio/ # Allocation logic and trade logging
│
├── reports/ # Generated backtest reports and plots
│
├── config/ # YAML configs and environment variables
│
└── main.py # Project entry point

yaml
Copy code

---

## 🚀 Installation  

Clone the repository and install dependencies:

```bash
git clone https://github.com/tobollie2/NEXORA.git
cd NEXORA
pip install -r requirements.txt
If you use a virtual environment (recommended):

bash
Copy code
python -m venv test_env
test_env\Scripts\activate
🧩 Pre-commit Automation
NEXORA uses pre-commit hooks to enforce code quality automatically.
Each commit runs black, flake8, isort, and mypy.

Set it up once:

bash
Copy code
pre-commit install
Run checks manually anytime:

bash
Copy code
pre-commit run --all-files
This ensures consistent style, imports, and static typing across the codebase.

🧪 Testing & Continuous Integration
GitHub Actions automatically run on every push or pull request.
The workflows handle:

✅ Linting & static type checks

🧠 Model validation & retraining

📊 Backtest regression tests

Run tests locally:

bash
Copy code
pytest -v
📈 Training and Optimization
Train regime-detection models:

bash
Copy code
python ai/train_regime_lstm.py
Run hyperparameter optimization experiments:

bash
Copy code
python -m optimization.optimizers.grid_search
Models and results are saved in ai/models/ and logs/reports/.

📊 Backtesting
To simulate and evaluate trading strategies:

bash
Copy code
python backtest/backtest_runner.py
Results include:

Equity curves

Performance metrics

Drawdown analysis

HTML summary reports

All output is saved in:

bash
Copy code
logs/reports/
🧠 Live Monitoring
Launch real-time monitoring and dashboards:

bash
Copy code
python monitoring/live_dashboard.py
You’ll get live analytics, strategy diagnostics, and regime-change alerts.

⚠️ Security
Sensitive credentials (API keys, database URIs, etc.) are stored in:

arduino
Copy code
config/secrets.env
This file is excluded from version control (.gitignore) to keep your secrets secure.

🪄 CI/CD Workflows
Workflow	Description	Status
NEXORA CI	Runs linting, tests, and static analysis	
NEXORA Model Retraining	Periodic model training verification	

🧭 Roadmap
 Add reinforcement learning-based regime allocator

 Extend data sources beyond Kraken

 Integrate distributed training (Ray / Dask)

 Add web dashboard for backtest visualization

 Package as pip-installable library

🤝 Contributing
Pull requests are welcome!
To contribute:

Fork this repo

Create a new feature branch

Ensure all pre-commit hooks pass

Submit a PR

📜 License
This project is licensed under the MIT License — see LICENSE for details.

🪶 Author
NEXORA Framework
Developed by tobollie2
AI-driven adaptive modeling and quantitative research.


