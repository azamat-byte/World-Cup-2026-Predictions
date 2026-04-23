#!/usr/bin/env python3
"""
World Cup 2026 Prediction Engine
Senior Sports Data Scientist Implementation
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sklearn.linear_model import PoissonRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class WorldCupPredictor:
    def __init__(self):
        self.results_df = None
        self.national_teams_df = None
        self.players_df = None
        self.valuations_df = None
        self.features_df = None
        self.poisson_model = None
        
    def load_data(self):
        """Load all datasets"""
        print("Loading datasets...")
        
        # Load international results
        self.results_df = pd.read_csv('International football results from 1872 to 2026/results.csv')
        self.results_df['date'] = pd.to_datetime(self.results_df['date'])
        
        # Load Transfermarkt data
        self.national_teams_df = pd.read_csv('Football Data from Transfermarkt/national_teams.csv')
        self.players_df = pd.read_csv('Football Data from Transfermarkt/players.csv')
        self.valuations_df = pd.read_csv('Football Data from Transfermarkt/player_valuations.csv')
        self.valuations_df['date'] = pd.to_datetime(self.valuations_df['date'])
        
        print(f"Results dataset: {len(self.results_df)} matches")
        print(f"National teams: {len(self.national_teams_df)} teams")
        print(f"Players: {len(self.players_df)} players")
        print(f"Valuations: {len(self.valuations_df)} records")
        
    def analyze_tournament_types(self):
        """Analyze tournament types to identify FIFA-recognized competitions"""
        print("\nAnalyzing tournament types...")
        
        # Get tournament counts
        tournament_counts = self.results_df['tournament'].value_counts()
        print("Top 20 tournament types:")
        print(tournament_counts.head(20))
        
        # FIFA-recognized tournaments (common ones)
        fifa_tournaments = [
            'FIFA World Cup', 'FIFA World Cup qualification', 
            'FIFA Confederations Cup', 'FIFA Club World Cup',
            'UEFA Euro', 'UEFA Euro qualification', 'UEFA Nations League',
            'Copa América', 'African Cup of Nations', 'AFC Asian Cup',
            'CONCACAF Gold Cup', 'OFC Nations Cup'
        ]
        
        # Also include friendly matches (FIFA-recognized)
        friendly_mask = self.results_df['tournament'] == 'Friendly'
        
        # Create mask for FIFA-recognized tournaments
        fifa_mask = self.results_df['tournament'].isin(fifa_tournaments) | friendly_mask
        
        print(f"\nFIFA-recognized matches: {fifa_mask.sum()} out of {len(self.results_df)}")
        
        return fifa_mask
    
    def filter_recent_matches(self, years=10):
        """Filter matches from last N years"""
        cutoff_date = datetime.now() - timedelta(days=years*365)
        recent_mask = self.results_df['date'] >= cutoff_date
        
        print(f"\nMatches in last {years} years: {recent_mask.sum()}")
        
        return recent_mask
    
    def clean_match_data(self):
        """Clean match history for FIFA-recognized internationals from last 10 years"""
        print("\nCleaning match data...")
        
        # Get FIFA-recognized tournaments
        fifa_mask = self.analyze_tournament_types()
        
        # Get recent matches
        recent_mask = self.filter_recent_matches(10)
        
        # Combine filters
        clean_mask = fifa_mask & recent_mask
        
        # Apply filtering
        self.clean_results = self.results_df[clean_mask].copy()
        
        print(f"Clean dataset: {len(self.clean_results)} matches")
        
        # Basic stats
        print(f"Date range: {self.clean_results['date'].min()} to {self.clean_results['date'].max()}")
        print(f"Unique teams: {len(set(self.clean_results['home_team'].unique()) | set(self.clean_results['away_team'].unique()))}")
        
        return self.clean_results
    
    def calculate_squad_values(self):
        """Calculate squad value for each nation from Transfermarkt data"""
        print("\nCalculating squad values...")
        
        # Get latest valuation for each player
        latest_valuations = self.valuations_df.loc[self.valuations_df.groupby('player_id')['date'].idxmax()]
        
        # Merge with players to get national team info
        players_with_valuation = latest_valuations.merge(
            self.players_df[['player_id', 'current_national_team_id', 'market_value_in_eur']],
            on='player_id',
            how='left'
        )
        
        # Filter for players with national teams
        players_with_national_team = players_with_valuation[
            players_with_national_team['current_national_team_id'].notna()
        ].copy()
        
        # Calculate squad values by national team
        squad_values = players_with_national_team.groupby('current_national_team_id').agg({
            'market_value_in_eur_y': ['sum', 'mean', 'count']
        }).reset_index()
        
        # Flatten column names
        squad_values.columns = ['national_team_id', 'total_market_value', 'avg_market_value', 'squad_size']
        
        # Merge with national teams data
        self.squad_values = squad_values.merge(
            self.national_teams_df[['national_team_id', 'name', 'total_market_value', 'fifa_ranking']],
            on='national_team_id',
            how='left',
            suffixes=('_calculated', '_transfermarkt')
        )
        
        # Use calculated value if available, otherwise use Transfermarkt value
        self.squad_values['final_squad_value'] = self.squad_values['total_market_value_calculated'].fillna(
            self.squad_values['total_market_value_transfermarkt']
        )
        
        print(f"Calculated squad values for {len(self.squad_values)} national teams")
        
        return self.squad_values
    
    def calculate_attack_defense_strength(self):
        """Calculate attack and defense strength using weighted rolling averages"""
        print("\nCalculating attack and defense strength...")
        
        # Create team-level statistics
        team_stats = {}
        
        # Get all unique teams
        all_teams = set(self.clean_results['home_team'].unique()) | set(self.clean_results['away_team'].unique())
        
        for team in all_teams:
            # Get matches where team played
            home_matches = self.clean_results[self.clean_results['home_team'] == team].copy()
            away_matches = self.clean_results[self.clean_results['away_team'] == team].copy()
            
            # Calculate goals scored and conceded
            home_matches['goals_scored'] = home_matches['home_score']
            home_matches['goals_conceded'] = home_matches['away_score']
            away_matches['goals_scored'] = away_matches['away_score']
            away_matches['goals_conceded'] = away_matches['home_score']
            
            # Combine home and away
            team_matches = pd.concat([home_matches, away_matches]).sort_values('date')
            
            # Calculate rolling averages (last 20 matches, weighted by recency)
            if len(team_matches) > 0:
                # Weight more recent matches more heavily
                weights = np.exp(np.linspace(-1, 0, len(team_matches)))
                weights = weights / weights.sum()
                
                # Attack strength: weighted average of goals scored
                attack_strength = np.average(team_matches['goals_scored'], weights=weights)
                
                # Defense strength: weighted average of goals conceded (lower is better)
                defense_strength = np.average(team_matches['goals_conceded'], weights=weights)
                
                # Recent form (last 5 matches)
                recent_form = team_matches.tail(5)
                recent_attack = recent_form['goals_scored'].mean()
                recent_defense = recent_form['goals_conceded'].mean()
                
                team_stats[team] = {
                    'attack_strength': attack_strength,
                    'defense_strength': defense_strength,
                    'recent_attack': recent_attack,
                    'recent_defense': recent_defense,
                    'matches_played': len(team_matches)
                }
        
        # Convert to DataFrame
        self.team_strengths = pd.DataFrame.from_dict(team_stats, orient='index').reset_index()
        self.team_strengths.columns = ['team_name', 'attack_strength', 'defense_strength', 
                                       'recent_attack', 'recent_defense', 'matches_played']
        
        print(f"Calculated strength metrics for {len(self.team_strengths)} teams")
        
        return self.team_strengths
    
    def merge_features(self):
        """Merge all features: squad values, rankings, attack/defense strength"""
        print("\nMerging all features...")
        
        # Merge team strengths with squad values
        features = self.team_strengths.merge(
            self.squad_values[['name', 'final_squad_value', 'fifa_ranking']],
            left_on='team_name',
            right_on='name',
            how='left'
        )
        
        # Handle missing values
        features['final_squad_value'] = features['final_squad_value'].fillna(0)
        features['fifa_ranking'] = features['fifa_ranking'].fillna(200)  # High rank for missing
        
        # Create normalized features
        scaler = StandardScaler()
        
        # Log transform squad value for normalization
        features['log_squad_value'] = np.log1p(features['final_squad_value'])
        
        # Normalize features
        numeric_cols = ['attack_strength', 'defense_strength', 'log_squad_value', 'fifa_ranking']
        features[numeric_cols] = scaler.fit_transform(features[numeric_cols])
        
        # Create overall strength score
        features['overall_strength'] = (
            features['attack_strength'] * 0.3 +
            (1 - features['defense_strength']) * 0.3 +  # Lower defense strength is better
            features['log_squad_value'] * 0.2 +
            (1 - features['fifa_ranking']) * 0.2  # Lower ranking number is better
        )
        
        self.features_df = features
        print(f"Final feature dataset: {len(self.features_df)} teams with {len(features.columns)} features")
        
        return self.features_df
    
    def prepare_model_data(self):
        """Prepare data for Poisson regression model"""
        print("\nPreparing model data...")
        
        # Create match-level features
        model_data = []
        
        for _, match in self.clean_results.iterrows():
            home_team = match['home_team']
            away_team = match['away_team']
            
            # Get team features
            home_features = self.features_df[self.features_df['team_name'] == home_team]
            away_features = self.features_df[self.features_df['team_name'] == away_team]
            
            if len(home_features) > 0 and len(away_features) > 0:
                home_feat = home_features.iloc[0]
                away_feat = away_features.iloc[0]
                
                # Host advantage (for USA, Mexico, Canada)
                host_advantage = 0
                if home_team in ['USA', 'United States', 'Mexico', 'Canada']:
                    host_advantage = 1
                
                # Create feature row
                model_data.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_goals': match['home_score'],
                    'away_goals': match['away_score'],
                    'home_attack': home_feat['attack_strength'],
                    'home_defense': home_feat['defense_strength'],
                    'away_attack': away_feat['attack_strength'],
                    'away_defense': away_feat['defense_strength'],
                    'home_squad_value': home_feat['log_squad_value'],
                    'away_squad_value': away_feat['log_squad_value'],
                    'home_fifa_rank': home_feat['fifa_ranking'],
                    'away_fifa_rank': away_feat['fifa_ranking'],
                    'host_advantage': host_advantage
                })
        
        self.model_data = pd.DataFrame(model_data)
        print(f"Model dataset: {len(self.model_data)} matches")
        
        return self.model_data
    
    def train_poisson_model(self):
        """Train Poisson regression model for goal prediction"""
        print("\nTraining Poisson regression models...")
        
        # Features for home goals
        home_features = ['home_attack', 'away_defense', 'home_squad_value', 'away_squad_value', 
                        'home_fifa_rank', 'away_fifa_rank', 'host_advantage']
        
        # Features for away goals  
        away_features = ['away_attack', 'home_defense', 'away_squad_value', 'home_squad_value',
                        'away_fifa_rank', 'home_fifa_rank']
        
        # Train home goals model
        X_home = self.model_data[home_features]
        y_home = self.model_data['home_goals']
        
        self.home_model = PoissonRegressor(alpha=0.1)
        self.home_model.fit(X_home, y_home)
        
        # Train away goals model
        X_away = self.model_data[away_features]
        y_away = self.model_data['away_goals']
        
        self.away_model = PoissonRegressor(alpha=0.1)
        self.away_model.fit(X_away, y_away)
        
        print("Models trained successfully")
        
        # Print model coefficients
        print("\nHome model coefficients:")
        for feat, coef in zip(home_features, self.home_model.coef_):
            print(f"  {feat}: {coef:.4f}")
        
        print("\nAway model coefficients:")
        for feat, coef in zip(away_features, self.away_model.coef_):
            print(f"  {feat}: {coef:.4f}")
    
    def predict_match(self, home_team, away_team, host_advantage=0):
        """Predict goals for a specific match"""
        # Get team features
        home_features = self.features_df[self.features_df['team_name'] == home_team]
        away_features = self.features_df[self.features_df['team_name'] == away_team]
        
        if len(home_features) == 0 or len(away_features) == 0:
            return None, None
        
        home_feat = home_features.iloc[0]
        away_feat = away_features.iloc[0]
        
        # Prepare features
        home_input = [[
            home_feat['attack_strength'], away_feat['defense_strength'],
            home_feat['log_squad_value'], away_feat['log_squad_value'],
            home_feat['fifa_ranking'], away_feat['fifa_ranking'],
            host_advantage
        ]]
        
        away_input = [[
            away_feat['attack_strength'], home_feat['defense_strength'],
            away_feat['log_squad_value'], home_feat['log_squad_value'],
            away_feat['fifa_ranking'], home_feat['fifa_ranking']
        ]]
        
        # Predict expected goals
        home_goals = self.home_model.predict(home_input)[0]
        away_goals = self.away_model.predict(away_input)[0]
        
        return home_goals, away_goals
    
    def run_initial_analysis(self):
        """Run the complete initial analysis"""
        print("=" * 60)
        print("WORLD CUP 2026 PREDICTION ENGINE - INITIAL ANALYSIS")
        print("=" * 60)
        
        # Step 1: Load and clean data
        self.load_data()
        self.clean_match_data()
        
        # Step 2: Calculate squad values
        self.calculate_squad_values()
        
        # Step 3: Calculate attack/defense strength
        self.calculate_attack_defense_strength()
        
        # Step 4: Merge features
        self.merge_features()
        
        # Step 5: Prepare model data
        self.prepare_model_data()
        
        # Step 6: Train models
        self.train_poisson_model()
        
        print("\n" + "=" * 60)
        print("INITIAL ANALYSIS COMPLETE")
        print("=" * 60)
        
        return self

if __name__ == "__main__":
    predictor = WorldCupPredictor()
    predictor.run_initial_analysis()
