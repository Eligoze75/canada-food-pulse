# Canada Food Pulse

> Exploring Canada's food scene through Yelp data: top cuisines, restaurants, peak hours, and neighbourhood hotspots visualized in an interactive Plotly Dash app.

**[Try the live dashboard!](https://859f9c80-f35f-4f6b-9d73-70e74c5e85e2.plotly.app/)**

---

## Objective & Mission

Canada Food Pulse is an interactive data dashboard that analyses Yelp review data for **Toronto** and **Montreal** to help users understand what makes a food business successful in those cities.

The mission is to turn raw review data into actionable insights for two audiences:

- **Aspiring restaurateurs** — discover which cuisines are underserved, which neighbourhoods have the highest foot traffic, and what segments perform best.
- **Food lovers** — find the top-rated spots, trending cuisines, and the best times to visit.

---

## User Stories & How the Dashboard Answers Them

| As a user I want to know… | Where to find it |
|---|---|
| Which cuisines are most popular in each city | Overview → Top 10 Cuisines (ranked by Popularity) |
| Which cuisines have the best ratings | Overview → Top 10 Cuisines (switch to Rating) · KPI "Best Rated Cuisine" |
| How many businesses exist per cuisine | Overview → Top 10 Cuisines (switch to Number of Businesses) |
| The overall rating distribution per city | Overview → Rating Distribution chart |
| Which cuisine is the biggest (volume vs quality) | Overview → Cuisine Landscape bubble chart |
| When restaurants are busiest during the day | Peak Hours → Traffic Heatmap (hour × weekday) |
| Which day of the week has the most traffic | Peak Hours → Busiest Day of the Week bar chart |
| Where restaurants and cafes are concentrated | Map → Density heatmap |
| Which neighbourhoods have the most places | Map → Most Places KPI cards |
| Which neighbourhoods have the highest-rated places | Map → Best Rated KPI cards |
| Which neighbourhoods offer the most cuisine variety | Map → Most Variety KPI cards |

All three pages share a **City** filter (Toronto / Montreal / Both) and a **Segment** filter (Restaurants, Cafes, Bars, Fast Food, Bakeries, Breakfast & Brunch, or All Food & Drink), so every chart can be scoped to the exact question at hand.

---

## Dashboard Pages

### Overview

The entry point. Provides a city-level summary of the food scene.

- **KPI cards** — Total Businesses, Avg Star Rating, Most Popular Cuisine, Best Rated Cuisine
- **Rating Distribution** — histogram of star ratings, overlaid by city when "Both" is selected
- **Top 10 Cuisines** — horizontal bar chart rankable by Popularity (total reviews), Rating (avg stars), or Number of Businesses
- **Cuisine Landscape: Volume vs Quality** — bubble chart where size = total reviews, x = number of businesses, y = avg rating. Reveals which cuisines are both high-volume and high-quality

### Peak Hours

Reveals traffic patterns by time of day and day of week.

- **Traffic Heatmap** — weekday × hour grid coloured by total check-ins. Instantly shows peak slots (e.g. Friday/Saturday evenings). Filterable by city and segment.
- **Busiest Day of the Week** — bar chart summarising total check-ins per weekday

### Map

Geographic view of the food landscape.

- **Density Heatmap** — Plotly density map weighted by review count, highlighting hotspot neighbourhoods over individual dots
- **Neighbourhood KPI cards** — top 3 neighbourhoods by Most Places, Best Rated (avg ★), and Most Variety (distinct cuisine count), all reactive to the city and segment filters

---

## Repository Structure

```bash
canada-food-pulse/
│
├── app.py
│
├── pages/
│   ├── overview.py
│   ├── peak_hours.py
│   └── map_view.py
│
├── scripts/
│   └── preprocess.py
│
├── notebooks/
│   ├── eda.ipynb
│   └── text_utils.py
│
├── data/
│   └── processed/
│       ├── yelp_business_data_cleaned.csv
│       ├── df_businesses.csv
│       ├── df_cuisine_stats.csv
│       └── df_peak_heatmap.csv
│
├── assets/
│   ├── style.css
│   └── canada_leaf.png
│
├── environment.yml
├── requirements.txt
├── Procfile
└── README.md
```

---

## Installation & Running Locally

### 1. Prerequisites

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/) installed

### 2. Clone the repository

```bash
git clone https://github.com/Eligoze75/canada-food-pulse.git
cd canada-food-pulse
```

### 3. Create and activate the conda environment

```bash
conda env create -f environment.yml
conda activate canada-food-pulse
```

### 4. Launch the app

```bash
python app.py
```

Open your browser at [http://127.0.0.1:8050](http://127.0.0.1:8050).

---

## Data Source

This project uses the **[Yelp Open Dataset](https://www.kaggle.com/datasets/yelp-dataset/yelp-dataset)**, available on Kaggle.

The dataset is used **strictly for educational purposes** as part of a data science coursework project. No commercial use is intended. All rights to the data belong to Yelp, Inc. Please refer to [Yelp's Dataset Terms of Use](https://terms.yelp.com/tos/en_us/20200101_en_us) before using it in your own projects.
