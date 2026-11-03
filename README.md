# FinSight Analytics

# Live Application: https://finsight-analytics099.streamlit.app/

### An Interactive Stock Market Analysis and Portfolio Management Platform

FinSight Analytics is a Python-based web application developed as part of the **Mastering Python for Finance** subject under the guidance of **Ms. Rekha Gaur**.

The platform provides an interactive environment for exploring Indian stock-market data, comparing companies, analysing financial performance and risk, and understanding portfolio behaviour.

It also includes an AI-powered financial assistant that helps users understand financial concepts through simple explanations.

---

## 1. Project Objectives

- To develop an interactive stock-market analysis platform using Python.
- To explore historical stock-price movements of selected Indian companies.
- To compare the performance of different stocks.
- To analyse financial performance and investment risk.
- To understand portfolio allocation and diversification.
- To present market information through interactive visualisations.
- To integrate an AI assistant for general financial explanations.

## 2. Key Features

### 1. Main Dashboard
Provides the main interface and navigation to the different sections of FinSight Analytics.

### 2. Stock Explorer
- Select and explore individual stocks.
- View historical stock-price movements.
- Analyse data using preset and custom date ranges.

### 3. Stock Comparison
- Compare multiple selected companies.
- Examine historical performance.
- View comparative charts and financial measures.

### 4. Performance & Risk
- Analyse historical returns.
- Examine volatility and risk.
- Understand risk-adjusted performance using the Sharpe Ratio.

### 5. Portfolio Lab
- Explore portfolio allocation.
- Analyse portfolio performance and risk.
- Understand diversification and relationships between assets.

### 6. Market Insights
- Explore selected market information.
- View stock and market-index trends.
- Understand market movements through visual summaries.

### 7. FinSight AI
- AI-powered financial question-and-answer interface.
- Explains financial concepts in simple language.
- Supports questions about stock markets, financial ratios, portfolio diversification and investment risk.
- Powered by the Google Gemini API.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development and financial calculations |
| Streamlit | Interactive web application |
| Pandas | Data processing and analysis |
| NumPy | Numerical calculations |
| Plotly | Interactive charts and visualisations |
| yfinance | Historical stock-market data retrieval |
| Yahoo Finance | Market data source |
| Google Gemini API | AI-powered financial assistant |

## 4. Project Structure

```text
FinanceProject/
│
├── pages/
│   ├── 1_Stock_Explorer.py
│   ├── 2_Stock_Comparison.py
│   ├── 3_Performance_Risk.py
│   ├── 4_Portfolio_Lab.py
│   ├── 5_Market_Insights.py
│   └── 6_FinSight_AI.py
│
├── .gitignore
├── ai_assistant.py
├── app.py
├── build.bat
├── common.py
├── DEMO_SCRIPT.md
├── finance_functions.py
├── README.md
├── requirements.txt
└── TESTING_CHECKLIST
```

### Description of Important Files

| File / Folder | Description |
|---|---|
| `app.py` | Main Streamlit application and dashboard entry point. |
| `ai_assistant.py` | Handles the Gemini API integration for FinSight AI. |
| `common.py` | Contains shared functions and configurations used across the application. |
| `finance_functions.py` | Contains stock-data retrieval and financial analysis functions. |
| `pages/` | Contains the six individual application modules. |
| `requirements.txt` | Lists the Python libraries required to run the project. |
| `build.bat` | Windows batch file for project setup or build tasks. |
| `DEMO_SCRIPT.md` | Contains the project demonstration script. |
| `TESTING_CHECKLIST` | Contains the project testing checklist. |
| `.gitignore` | Specifies files and folders that should not be uploaded to GitHub. |

## 5. Installation and Setup

Follow these steps to run the application locally.

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

### Step 2: Navigate to the Project Folder

```bash
cd FinanceProject
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure the Gemini API Key

Create a folder named `.streamlit` in the project directory if it does not already exist.

Inside it, create a file named `secrets.toml` and add:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
```

Replace the placeholder with your own Gemini API key.

**Important:** Never upload your actual `secrets.toml` file or API key to GitHub.

### Step 5: Run the Application

```bash
streamlit run app.py
```

The application will open in your web browser.

## 6. Data Source

Historical stock-market information is retrieved using the `yfinance` Python library, which accesses data available through Yahoo Finance.

Data availability and timing depend on the external provider. The application is intended for educational and analytical purposes.

## 7. Financial Measures

The application uses selected financial measures, including:

- Daily and cumulative returns
- Annualised returns
- Annualised volatility
- Sharpe Ratio
- Portfolio weights
- Portfolio returns
- Portfolio risk and diversification analysis

## 8. Limitations

- The application depends on external market-data availability.
- The available stock universe is limited to the companies included in the application.
- Historical performance does not guarantee future returns.
- The AI assistant may occasionally generate inaccurate or incomplete explanations.
- The AI assistant currently provides general financial explanations and is not connected to live dashboard data.
- The platform does not execute trades or provide personalised investment advice.

## 9. Future Scope

- Add more Indian listed companies and market indices.
- Include additional technical indicators and fundamental ratios.
- Connect the AI assistant to selected dashboard data.
- Introduce user accounts and saved portfolios.
- Improve data validation and analytical features.

## 10. Disclaimer

FinSight Analytics is an educational project developed for the **Mastering Python for Finance** subject. It demonstrates the application of Python programming and financial concepts. It should not be considered professional investment advice or a trading recommendation.

---

## Project Information

Project Name: FinSight Analytics
Subject: Mastering Python for Finance
Developed by: Sneha Chaudhary
Programme: BBA – Finance
