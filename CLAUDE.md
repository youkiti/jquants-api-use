# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a J-Quants API development repository for working with Japanese stock market data. It includes both a Jupyter notebook for tutorials and a Python script for automated stock metrics retrieval.

## Repository Structure

- `jquants_api_quick_start.ipynb` - Jupyter notebook with J-Quants API tutorials
- `fetch_stock_metrics_with_valuation.py` - **Main script** for fetching stock data
- `quants-codes.txt` - List of stock codes to analyze (17 Japanese stocks)
- `output/` - Output folder for CSV results (gitignored)
- `venv/` - Virtual environment (gitignored)
- `.env` - API credentials (gitignored)
- `requirements.txt` - Python dependencies

## Main Development Commands

### Setup
```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure API credentials
cp .env.example .env
# Edit .env with your J-Quants API credentials
```

### Running Stock Analysis
```bash
# Activate virtual environment and run main script
source venv/bin/activate && python fetch_stock_metrics_with_valuation.py
```

## Key Features

### Stock Metrics Script
The main script (`fetch_stock_metrics_with_valuation.py`) fetches:
- **Latest stock prices** (Close price from 2024-12-30)
- **PER (Price-to-Earnings Ratio)** - Both current and forecast
- **PBR (Price-to-Book Ratio)** - Current ratio
- **Company names** - Japanese company names

### Output
- Results saved to `output/stock_metrics_YYYYMMDD_HHMMSS.csv`
- Console display with formatted table
- All CSV files are gitignored for clean repository

### API Endpoints Used
- `/listed/info` - Company information
- `/prices/daily_quotes` - Stock price data
- `/fins/statements` - Financial statements for PER/PBR calculation

## Security Notes
- API credentials stored in `.env` file (gitignored)
- Supports both refresh token and email/password authentication
- Output files automatically excluded from git
- Never commit sensitive data