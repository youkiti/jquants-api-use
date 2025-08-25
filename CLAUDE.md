# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a J-Quants API development repository for working with Japanese stock market data. The main content is a Jupyter notebook (`jquants_api_quick_start.ipynb`) that demonstrates how to use the J-Quants API to fetch and analyze Japanese financial market data.

## Repository Structure

- `jquants_api_quick_start.ipynb` - Main Jupyter notebook with J-Quants API examples and tutorials
- `.env` - Environment variables for API credentials (gitignored)
- `README.md` - Basic project description in Japanese

## Key Development Tasks

### Running the Notebook
The notebook is designed to run in Google Colab and includes:
- Initial setup and imports
- Google Drive mounting for secure credential storage
- API authentication and token management
- Examples of fetching various market data (daily quotes, trading calendar, etc.)

### API Endpoints
The notebook demonstrates usage of J-Quants API endpoints including:
- `/prices/daily_quotes` - Stock price data (adjusted and unadjusted)
- `/market/trading_calendar` - Trading calendar information for TSE and OSE

## Security Notes
- API credentials should be stored in `.env` file (which is gitignored)
- The notebook uses Google Drive for secure credential storage when running in Colab
- Never commit API keys or tokens directly in code