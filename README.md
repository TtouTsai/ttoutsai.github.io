# YICLIC - Intelligent Food Recommendation System

An intelligent food recommendation platform that combines machine learning and natural language processing, utilizing Google Maps review analysis, BERT food review filtering, GPT automatic scoring, and time-weighted ranking to help users find the best restaurants.

## Project Overview

YICLIC is a fully automated restaurant review analysis system that integrates the following core features:

- **Google Maps Review Scraping**: Automatically fetches all reviews for target restaurants
- **Intelligent Content Filtering**: Uses BERT models to filter reviews truly related to food
- **GPT Automatic Scoring**: Leverages GPT-4 semantic understanding to score food quality on a 1-5 scale
- **Time-Weighted Ranking**: Employs Dirichlet-Thompson Bayesian scoring with time decay weights
- **Interactive Map Interface**: Visualizes recommendation results

## Quick Start

### 1. Environment Setup

#### Install Python Packages

```bash
cd backend
pip install google-search-results openai chardet
pip install transformers torch jieba scipy pandas numpy tqdm
pip install fastapi uvicorn pydantic
pip install fastparquet
pip install --upgrade safetensors
```

#### Configure API Keys

This system requires two API keys:

**Windows Setup:**

1. Open "System Properties" → "Advanced" → "Environment Variables"
2. Add new user variables:
   - Variable name: `SERPAPI_API_KEY`, Value: Your SerpAPI Key
   - Variable name: `GPT_API_KEY`, Value: Your OpenAI API Key
3. Restart your terminal or VS Code

**Verify Setup:**

```bash
# Execute in terminal
echo %SERPAPI_API_KEY%
echo %GPT_API_KEY%
```

### 2. Start Backend Service

```bash
cd backend
uvicorn api:app --reload
```

Upon successful startup, you should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3. Open Frontend Page

Open `https://ttoutsai.github.io/YICLIC.html` in your browser

## User Guide

### Basic Operations

1. **Enter Search Keywords**
   - Type location + food type in the search box (e.g., "Taipei Ramen", "Taichung Hot Pot")
   - Press Enter or click the search button

2. **Wait for Analysis Completion**
   - The system will automatically execute the following workflow:
     - Scrape reviews from Google Maps
     - BERT model filters food-related reviews
     - GPT-4 automatic scoring
     - Calculate Dirichlet-Thompson ranking scores

3. **View Recommendation Results**
   - Recommended restaurants will be marked on the map
   - Hover over markers to view detailed restaurant information
   - The area below the map displays Top 5 recommended restaurants