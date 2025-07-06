# Sports Betting Arbitrage Identifier

This notebook identifies arbitrage opportunities across a range of bookmakers using live market odds from [`the-odds-api`](https://the-odds-api.com/).

Arbitrage opportunities are detected using the following techniques:
1. **N-event arbitrage (Head-to-head)**
2. **Back-Lay arbitrage**
3. **Lay-all arbitrage**
4. **Other market inefficiencies**

---

## Project Setup

### Requirements

This project requires Python 3.8+ and the following packages:

- requests
- PyYAML
- pandas
- numpy
- scipy
- ipywidgets
- ipython

You can install all dependencies using:

```sh
pip install -r requirements.txt
```

---

## Notebook Structure

1. Read local imports
2. Load configuration and set global variables
3. Query active sports via API
4. Choose one of the following data collection modes:
   - (1) Gather odds for a specific sport
   - (2) Gather odds for all active sports

---

## API Setup

This notebook uses the following API:

- Base URL: `https://the-odds-api.com/`  
- Docs: [SwaggerHub - the-odds-api](https://app.swaggerhub.com/apis-docs/the-odds-api/odds-api/4#/current%20events/get_v4_sports__sport__odds)

---

##  Arbitrage Example — N-Event Arbitrage

Consider a market with three outcomes:

- Outcome A (Team A wins): Odds = $2 → `Oa`
- Outcome B (Team B wins): Odds = $3 → `Ob`
- Outcome C (Draw): Odds = $9 → `Oc`

To identify arbitrage, calculate the total implied probability:
1/Oa + 1/Ob + 1/Oc = 1/2 + 1/3 + 1/9 = 0.9444 (or 94.44%)

Since the total is **less than 100%**, an arbitrage opportunity exists.

How to Profit from This Mispricing?

Assume a total betting capital `Tb = $1000`.

#### Step 1: Calculate minimum position per outcome
Each outcome must return at least the total bet.

- A: MinBet = 1000 / 2 = $500.00
- B: MinBet = 1000 / 3 = $333.33
- C: MinBet = 1000 / 9 = $111.11

#### Step 2: Calculate max feasible bet per position
Ensure total outlay stays within $1000.

- A: MaxBet = 1000 - 333.33 - 111.11 = $555.56
- B: MaxBet = 1000 - 500.00 - 111.11 = $388.89
- C: MaxBet = 1000 - 500.00 - 333.33 = $166.67

#### Step 3: Validate feasibility
Total min bets = $500.00 + $333.33 + $111.11 = **$944.44**  
This is under $1000, so a feasible arbitrage strategy exists.

---

### Example Payouts  

| Bet     | Amount | Payout Calculation     | Net Profit | ROI  |
|----------|--------|-------------------------|------------|------|
| Outcome A | $520   | 520 × 2 - 1000 = 1040 - 1000 | $40        | 4.0% |
| Outcome B | $360   | 360 × 3 - 1000 = 1080 - 1000 | $80        | 8.0% |
| Outcome C | $120   | 120 × 9 - 1000 = 1080 - 1000 | $80        | 8.0% |
   
This strategy results in a **guaranteed profit**, regardless of the outcome.  
**Exchange fees** can be include in this model by adjusting the raw odds by: 1 + (Odds - 1)*(1 + exchange fees) = O1a (Amended Odds)

---

## Arbitrage Example — Back-Lay Arbitrage  

This strategy exploits pricing differences between **back** markets (betting for an outcome) and **lay** markets (betting against the same outcome) across different bookmakers or exchanges.

### Strategy Logic

If: 
- Back Odd > Lay Odd (without fees)
- ((Back Odd - 1) * (1 - commission)) / (Lay Odd - 1) >= 1 (with fees)

…then an arbitrage opportunity may exist.

Why?  
You can:
- **Back** a team to win at higher odds with a traditional bookmaker.
- **Lay** the same team at lower odds on a betting exchange.
- Properly stake each leg to guarantee a profit or minimise loss, regardless of outcome.

### Example

Let's say we're analysing **Team A** in a head-to-head (H2H) market:

**Event**: Team A vs Team B  
**Market**: Head-to-Head  
**Target Outcome**: Team A wins

| Bet Type | Odds | Platform         |
|----------|------|------------------|
| Back     | 3.4  | Bookmaker        |
| Lay      | 3.2  | Betting Exchange |
| Commission | 5% | on net lay winnings |

#### Arbitrage Condition:
\[
\text{Lay Odds (3.2)} < \text{Back Odds (3.4)} \Rightarrow \text{Opportunity detected}
\]

### Staking Example

Assume:
- Total back stake = $100 on Team A at odds of 3.4
- Lay odds = 3.2
- Let’s find the lay stake to **match liability**:

#### Step 1: Calculate Lay Stake

We want both outcomes to return roughly the same:
Lay Stake = (Back Stake × Back Odds) / (Lay Odds)
= (100 × 3.4) / 3.2
= 106.25

#### Step 2: Calculate Lay Liability
Liability = (Lay Odds - 1) × Lay Stake
= (3.2 - 1) × 106.25
= 2.2 × 106.25 = $233.75

### Profit Scenarios

| Outcome      | Back Bet (Stake = $100, Odds = 3.4) | Lay Bet (Stake = 106.25, Odds = 3.2) | Net Result      |
|--------------|-------------------------------------|---------------------------------------|-----------------|
| Team A Wins  | Win: 100 × (3.4 - 1) = $240         | Lose: -$233.75                        | **Profit = $6.25** |
| Team A Loses | Lose: -$100                         | Win: +$106.25                         | **Profit = $6.25** |

**Risk-free profit of $6.25 on a $233.75 exposure (Team A wins) or $100 exposure (Team A loses).**

---

## Arbitrage Example — Lay-All Arbitrage

This strategy explores whether you can profit by **laying all possible outcomes** of a multi-event market (e.g., Team A, Team B, Draw), typically on a betting exchange.

### Strategy Logic

When laying each outcome, you take the position of "the bookmaker", offering to pay out winnings to other bettors.  
To secure an arbitrage, your **total liabilities must be less than your collected bets** (minus exchange fees, if applicable).

The strategy:
- Identifies the **optimal stake size** for each lay bet.
- Ensures total stake does not exceed a budget (e.g., $100).
- Solves for all possible outcomes such that **you win regardless of which event occurs**.

> This strategy is particularly useful in **3-way markets** (like soccer), but can extend to **N outcomes**.

### Example Inputs

- Lay Odds: [2.0, 3.0, 5.0]
- Fee: 0% (i.e., no commission)
- Total stake: $100

### Optimal Lay Bets (calculated using SLSQP optimisation)

| Outcome | Lay Odds | Bet Size |
|---------|----------|----------|
| Team A  | 2.0      | $46.67   |
| Team B  | 3.0      | $33.33   |
| Draw    | 5.0      | $20.00   |

### Profit Per Outcome

| Outcome | Net Profit |
|---------|-------------|
| Team A  | $6.66       |
| Team B  | $0.01       |
| Draw    | $0.00       |


### Profit Mechanics

When you lay a bet:
- You collect another bettor’s stake upfront.
- If that outcome doesn’t occur, you keep their stake.
- If it does occur, you pay out based on the odds.

In this example:
- No matter the match result, your **liability is covered**, and you're left with a **guaranteed break-even or profit**