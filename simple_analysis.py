import pandas as pd
import numpy as np

# Load datasets
print("Loading datasets...")

# Load international results
results_df = pd.read_csv('International football results from 1872 to 2026/results.csv')
results_df['date'] = pd.to_datetime(results_df['date'])

print(f"Results dataset: {len(results_df)} matches")
print(f"Date range: {results_df['date'].min()} to {results_df['date'].max()}")

# Analyze tournament types
print("\nTop 20 tournament types:")
tournament_counts = results_df['tournament'].value_counts()
print(tournament_counts.head(20))

# Filter recent matches (last 10 years)
cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=10*365)
recent_mask = results_df['date'] >= cutoff_date
recent_results = results_df[recent_mask]

print(f"\nMatches in last 10 years: {len(recent_results)}")

# FIFA-recognized tournaments
fifa_tournaments = [
    'FIFA World Cup', 'FIFA World Cup qualification', 
    'FIFA Confederations Cup', 'FIFA Club World Cup',
    'UEFA Euro', 'UEFA Euro qualification', 'UEFA Nations League',
    'Copa América', 'African Cup of Nations', 'AFC Asian Cup',
    'CONCACAF Gold Cup', 'OFC Nations Cup'
]

friendly_mask = recent_results['tournament'] == 'Friendly'
fifa_mask = recent_results['tournament'].isin(fifa_tournaments) | friendly_mask

clean_results = recent_results[fifa_mask]

print(f"FIFA-recognized matches in last 10 years: {len(clean_results)}")

# Load Transfermarkt data
national_teams_df = pd.read_csv('Football Data from Transfermarkt/national_teams.csv')
print(f"\nNational teams: {len(national_teams_df)} teams")

# Show some sample data
print("\nSample clean results:")
print(clean_results.head())

print("\nSample national teams:")
print(national_teams_df[['name', 'total_market_value', 'fifa_ranking']].head(10))

print("\nAnalysis complete!")
