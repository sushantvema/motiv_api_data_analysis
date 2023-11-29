# motiv_api_data_analysis
Author: Sushant Vema

Analysis Software for Motiv API Queries. An object-oriented EDA system to work with Motiv API results.

## Setup
Install required packages and dependencies with 
```python
pip install -r requirements.txt
```

## Data
This package prevents .csv files from being committed to git. Make sure to add `load_RANDOM_NAME.csv` and `pv_RANDOM_NAME.csv` to `motiv_data/data_we_gave_to_motiv/`

It's important to have "load" and "pv" be the first words of the file titles respectively. 

## Running
Run the script on the command line with 
```bash
python analysis.py motiv_data
```

Running this command assumes you have setup `motiv_data/` as per above.

## Expected Behavior
This script will:
1. Take synthetic csv files with load and pv inputs and match them to the appropriate API response JSON according to nearest-minute matching with timestamps. 
2. Standardize all datetimes to UTC (PST+8)
3. Scrape the most relevant single measurement from each subheading of the API response JSON. Here's a mapping of what is currently being queried out of the JSON dump as well as a subjective interpretation of units, etc:
    - ChargeDischargeCounter -> (DischargeCount, ChargeCount) 
        - Counting how many times the battery is charging or discharging?
    - 1MinPVAverager -> Averager
        - Assuming the units of Averager is kW or W
    - BatteryMeter -> ACPowerWattsSigned
        - Signed 3-phase real power in watts
    - PrimaryGridMeter -> ACPowerWattsSigned
        - Signed 3-phase real power in watts
    - ArbiterPower -> 
    - PVChargeLimiter ->
    - PVMeter ->
    - Distributer1 -> 
    - GEM100 ->
    - MaxAvgGrid ->
    - 1MinBatteryAverager ->
    - DemandManagement1 ->
    - 15MinGridAverager ->
    - 1MinGridLessBatteryAverager ->
4. Create insightful visualizations.
    1. Plot synthetic load and pv over time
    2. 