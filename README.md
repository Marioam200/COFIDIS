## Cofidis Racing Analytics

A cycling race difficulty analysis tool for the **Cofidis** team, based on the current UCI ranking and race winner history from ProCyclingStats.

---

## Description

This project automatically scrapes the UCI rider rankings and race calendar from [ProCyclingStats](https://www.procyclingstats.com/), cross-references the data with Cofidis' race schedule, and generates a **difficulty score (0–10)** for each race, recalibrated exclusively based on the races the team will compete in.

---

## Tech Stack

| Library | Purpose |
|---|---|
| `pandas` | Data processing and analysis |
| `selenium` | Dynamic web scraping (ProCyclingStats) |
| `beautifulsoup4` | HTML table extraction |
| `streamlit` | Interactive web interface |
| `webdriver-manager` | Automatic ChromeDriver management |

---

## Project Structure

```
TRABAJO_MDP/
├── app.py                              # Main Streamlit interface
├── scraper_calendario.py               # UCI 2025 calendar scraper
├── scraper_ranking.py                  # Full PCS ranking scraper
├── data/
│   ├── upcoming_races_cofidis.csv          # Cofidis race schedule
│   ├── calendario_uci_2025.csv             # Global UCI calendar (generated)
│   ├── PCS_Ranking_Completo.csv            # Full UCI ranking (generated)
│   ├── PCS_Ranking_Con_Nota.csv            # Ranking with scores (generated)
│   └── calendario_uci_2025_con_notas.csv   # Final output with scores
└── requirements.txt
```
---

##  Installation

```bash
# 1. Clone the repository
git clone https://github.com/Marioam200/TRABAJO_MDP.git
cd TRABAJO_MDP

# 2. Install dependencies
pip install -r requirements.txt
requirements.txt:
````
## Usage

### 1. Fetch the full UCI ranking
```bash
python scraper_ranking.py
````

Generates data/PCS_Ranking_Completo.csv with the updated ranking of all riders.


### 2. Fetch the UCI 2025 calendar

```bash
python scraper_calendario.py
````
Generates data/calendario_uci_2025.csv with all races and their winners.


### 3. Launch the app
```bash
streamlit run app.py
````
Opens the web interface. Select a race from the Cofidis calendar and get its difficulty score.


##  How is the difficulty score calculated?

1. Each UCI rider is assigned a **score from 0 to 10** based on their ranking position (higher rank → higher score).
2. The global calendar is cross-referenced with that score using the **previous year's winner** as a reference.
3. The score is **recalibrated** based solely on Cofidis' race schedule:
   - The hardest race in their calendar becomes **10**
   - The easiest race becomes **0**

---

##  Interface

The Streamlit app allows you to:
- Select a race from the Cofidis 2026 calendar
- Get the recalibrated difficulty score instantly
- Visualize key metrics directly in the browser

---

## Author

**Mario Alvarez Martinez**
- GitHub: [@Marioam200](https://github.com/Marioam200)

---

## License

Academic/professional use only. All rights reserved.
