# World Cup 2026 Prediction Engine - Data Cleaning Strategy

## Dataset Overview

### 1. International Football Results (49,289 matches)
- **Time Period:** 1872-11-30 to 2026-06-27
- **Key Columns:** date, home_team, away_team, home_score, away_score, tournament, city, country, neutral
- **Quality:** Complete dataset with future 2026 World Cup matches included

### 2. Transfermarkt National Teams (120 teams)
- **Key Features:** total_market_value, fifa_ranking, squad_size, average_age, confederation
- **Market Value Range:** €935K (San Marino) to €100M+ (top nations)

### 3. Transfermarkt Players & Valuations
- **Players:** 47,704 records with market values
- **Valuations:** 616,379 historical valuation records
- **Coverage:** Comprehensive player market value data

## Cleaning Strategy

### Phase 1: Match History Cleaning

#### 1.1 Date Filtering
- **Target Period:** Last 10 years (2016-04-22 to 2026-04-22)
- **Rationale:** Recent form more predictive for World Cup performance
- **Expected Reduction:** ~70% of historical matches

#### 1.2 Tournament Filtering
**FIFA-Recognized Tournaments:**
- FIFA World Cup
- FIFA World Cup qualification
- FIFA Confederations Cup
- Friendly matches (FIFA-recognized)
- UEFA Euro and qualification
- UEFA Nations League
- Copa América
- African Cup of Nations
- AFC Asian Cup
- CONCACAF Gold Cup
- OFC Nations Cup

**Exclusion Criteria:**
- Regional sub-tournaments
- Non-FIFA competitions
- Youth tournaments
- Women's tournaments (separate category)

#### 1.3 Data Quality Checks
- Remove matches with missing scores
- Verify team name consistency
- Handle neutral venue flags correctly
- Check for duplicate matches

### Phase 2: Squad Value Calculation

#### 2.1 Player Valuation Aggregation
**Methodology:**
1. Extract latest market value for each player
2. Filter by current national team assignment
3. Calculate squad metrics:
   - Total market value
   - Average market value per player
   - Squad size (players with valuations)
   - Value distribution (top 11 vs full squad)

#### 2.2 Data Integration
**Primary Source:** Calculated values from player data
**Fallback:** Transfermarkt provided squad values
**Validation:** Cross-reference between sources

### Phase 3: Feature Engineering

#### 3.1 Attack Strength Calculation
**Formula:** Weighted rolling average of goals scored
- Base weight: Last 20 matches
- Recent emphasis: Exponential decay factor
- Home/away differentiation
- Tournament importance weighting

#### 3.2 Defense Strength Calculation  
**Formula:** Weighted rolling average of goals conceded
- Inverse of attack strength (lower = better)
- Same weighting methodology
- Clean sheet bonus weighting

#### 3.3 Composite Features
**Normalization:**
- Log transformation for market values
- Z-score normalization for all features
- Min-max scaling for final integration

**Feature Set:**
- Attack Strength (normalized)
- Defense Strength (normalized)
- Squad Value (log-transformed)
- FIFA Ranking (inverse normalized)
- Recent Form (last 5 matches)
- Host Advantage (binary for USA/Mexico/Canada)

## Quality Assurance

### Validation Checks
1. **Team Coverage:** Ensure all World Cup qualifiers have data
2. **Temporal Consistency:** Verify date ranges are logical
3. **Value Ranges:** Check for outliers in market values
4. **Ranking Correlation:** Validate FIFA rankings vs performance

### Missing Data Handling
- **Squad Values:** Use regional averages for missing teams
- **Recent Form:** Use historical averages for new teams
- **Rankings:** Assign default rank (200) for unranked teams

## Expected Output

### Cleaned Dataset
- **Matches:** ~8,000-12,000 FIFA-recognized matches
- **Teams:** ~150-200 national teams with complete data
- **Features:** 8-10 normalized features per team

### Feature Matrix
```
Team | Attack_Str | Defense_Str | Squad_Value | FIFA_Rank | Recent_Form | Host_Adv
-----|------------|-------------|-------------|-----------|-------------|----------
BRA  | 1.23       | 0.87        | 2.45        | 0.15      | 1.12        | 0
USA  | 0.98       | 1.02        | 1.87        | 0.45      | 0.95        | 1
...
```

This cleaned dataset will serve as the foundation for the Poisson regression model and tournament simulation.
