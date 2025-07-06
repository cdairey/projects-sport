from scipy.optimize import minimize
import pandas as pd
import numpy as np
import logging

# configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Calculate the best odds on the market
def best_market_odds(
        market_odds:dict
    ) -> list:
    """
    This function aims to return a dict of the current best odds for a given market
    """

    # Create market odds dataframes
    odds_df = pd.DataFrame(market_odds)
    h2h_odds_df = odds_df[odds_df['market'].isin(['h2h', 'h2h_lay'])]
    other_df = odds_df[~odds_df["market"].isin(["h2h", "h2h_lay"])]
    distinct_match_markets = list(odds_df["market"].unique())

    # Loop through markets
    best_odds = []
    for market in distinct_match_markets:

        if market == "h2h" or market == "h2h_lay":

            distinct_match_outcomes = list(h2h_odds_df["name"].unique())
            # Loop through each outcome and find the best odds
            for outcome in distinct_match_outcomes:

                filtered_df = h2h_odds_df[(h2h_odds_df["market"] == market) & (h2h_odds_df["name"] == outcome)]
                if not filtered_df.empty:
                    best_price = max(filtered_df["price"])
                    company = list(filtered_df[filtered_df["price"] == best_price]["company"].unique())

                    # Create a dict of the best odds
                    outcome_best_odds = {
                        "market": market,
                        "outcome": outcome,
                        "price": best_price,
                        "impliedLikelihood": round(1/best_price,8),
                        "site":company
                    }
                    best_odds.append(outcome_best_odds)
        else: 
                # Find best outcome for other markets
                distinct_match_outcomes = list(other_df["name"].unique())
                distinct_match_point = list(other_df["point"].unique())

                for outcome in distinct_match_outcomes:
                    for point in distinct_match_point:

                        if point:                          
                            filtered_df = other_df[(other_df["market"] == market) & (other_df["name"] == outcome) & (other_df['point'] == point)]
                            if not filtered_df.empty:
                                best_price = max(filtered_df["price"])
                                company = list(filtered_df[filtered_df["price"] == best_price]["company"].unique())

                                outcome_best_odds = {
                                    "market": market,
                                    "outcome": outcome,
                                    "price": best_price,
                                    "point": point,
                                    "impliedLikelihood": round(1/best_price,8),
                                    "site":company
                                }
                                best_odds.append(outcome_best_odds)
    return best_odds


# Strategy h2h
def strategy_h2h(
        best_odds:pd.DataFrame
    ) -> dict:
    """
    This strategy is used to find arbs that exists for generic h2h markets
    """
    # h2h strategy
    h2h_chance = sum(best_odds[best_odds['market']=='h2h']['impliedLikelihood'])
    if h2h_chance < 1:
        result = {
            'strategy': 'h2h',
            'outcome': h2h_chance
        }
        return result
    else:
        return None


# Other Markets
def strategy_other(
        best_odds:pd.DataFrame
    )-> list:
    """
    This strategy is used to find arbs that exists for point markets
    """
    result = []
    points_df = best_odds[~best_odds["market"].isin(["h2h", "h2h_lay"])]
    point_markets = list(points_df["market"].unique())
    for market in point_markets:
        market_df = points_df[points_df["market"] == market]
        distinct_point = list(abs(market_df["point"]).unique())
        for point in distinct_point:
            point_negative = -point
            chance = sum(market_df[market_df['point'].isin([point_negative,point])]['impliedLikelihood'])
            if chance < 1:
                result.append({
                    "market": market,
                    "point": point,
                    "outcome": chance,
                })

    if result != []:
        return result
    else:
        return None

# Strategy back lay
def strategy_lay(
        best_odds:pd.DataFrame
    )-> list:
    """
    This strategy is used to find arbs that exists for lay markets
    """
    opps = []
    if best_odds[(best_odds['market']=='h2h_lay')].empty is False:

        distinct_outcomes = list(best_odds['outcome'].unique())

        for outcome in distinct_outcomes:

            back_odds = best_odds[(best_odds['market']=='h2h') & (best_odds['outcome']==outcome)]['price'].max()
            lay_odds = best_odds[(best_odds['market']=='h2h_lay') & (best_odds['outcome']==outcome)]['price'].min()

            # check if lay_odds < back_odds
            if lay_odds < back_odds:
                result = {
                    'strategy': 'lay',
                    'team': outcome,
                    'backOdds': back_odds,
                    'layOdds': lay_odds
                }
                opps.append(result)

        return opps
    else:
        return None


def strategy_all_lay(df: pd.DataFrame, total_stake=100, fee=0.0):
    """
    Solves N-way lay arbitrage from a DataFrame with lay odds.

    Parameters:
        df: DataFrame with columns ['market', 'outcome', 'price']
        total_stake: Total capital to allocate
        fee: Lay fee (as decimal)

    Returns:
        Dict with optimal stakes and profits per outcome if arbitrage exists; else None
    """
    # Filter to lay market
    lay_df = df[df['market'] == 'h2h_lay'].copy()
    
    if lay_df.empty:
        return None

    outcomes = lay_df['outcome'].tolist()
    lay_odds = lay_df['price'].tolist()
    N = len(lay_odds)
    profit_remaining = 1 - fee

    def objective(bets):
        return sum(bets)

    def outcome_constraint(i):
        def constraint(bets):
            payout = 0
            for j in range(N):
                if j == i:
                    payout -= bets[j] * (lay_odds[j] - 1)
                else:
                    payout += bets[j] * profit_remaining
            return payout
        return constraint

    def constraint_total_stake(bets):
        return sum(bets) - total_stake

    constraints = [{'type': 'ineq', 'fun': outcome_constraint(i)} for i in range(N)]
    constraints.append({'type': 'eq', 'fun': constraint_total_stake})

    bounds = [(0, total_stake)] * N
    initial_guess = [total_stake / N] * N

    result = minimize(objective, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)

    if result.success:
        bets = [round(x, 2) for x in result.x]
        profits = []
        for i in range(N):
            profit = 0
            for j in range(N):
                if j == i:
                    profit -= bets[j] * (lay_odds[j] - 1)
                else:
                    profit += bets[j] * profit_remaining
            profits.append(round(profit, 2))

        return {
            'outcomes': outcomes,
            'lay_odds': lay_odds,
            'bets': bets,
            'profits_per_outcome': dict(zip(outcomes, profits)),
            'is_arbitrage': all(p >= 0 for p in profits)
        }
    else:
        return None


# function used to consolidate arbs
def get_arbs(
        best_odds:list
    )-> list:
    """
    This function is used to execute all arbs at once
    """
    arbs = []
    best_odds_df = pd.DataFrame(best_odds)

    # Try stategy one (h2h)
    h2h = strategy_h2h(best_odds_df)
    if h2h is not None and h2h != []:
        arbs.append(h2h)

    # Try stategy two (back_lay)
    back_lay = strategy_lay(best_odds_df)
    if back_lay is not None and back_lay != []:
        arbs.append(back_lay)

    # Try stategy three (all_lay)
    all_lay = strategy_all_lay(best_odds_df)
    if all_lay is not None and all_lay != []:
        arbs.extend(all_lay)

    # try other strat 
    other = strategy_other(best_odds_df)
    if other is not None and other != []:
        arbs.extend(other)

    return arbs


# Single Market View
def summary_market(
        current_market_odds:dict
    )-> list:
    """
    This function aims to return a summarised view of market odds
    """

    market_details = []
    for match in current_market_odds:

        sport_key = match["sport_key"]
        sport_title = match["sport_title"]
        commence_time = match["commence_time"]
        home_team = match["home_team"]
        away_team = match["away_team"]
        match_market = []
        arbs = []
        # Loop through each book maker
        if match["bookmakers"] != []:
            for book_maker in match["bookmakers"]:

                company = book_maker["title"]

                # Loop through each market
                for market in book_maker["markets"]:

                    odds_offered_time = market["last_update"]
                    
                    # Loop through each outcome
                    for outcome in market["outcomes"]:

                        try:
                            point = outcome["point"]
                        except:
                            point = None

                        odds = {
                            "company": company,
                            "market": market["key"],
                            "name": outcome["name"],
                            "price": outcome["price"],
                            "point": point
                        }
                        match_market.append(odds)

            # Get market best odds
            best_odds = best_market_odds(match_market)

            # get arbs
            try:
                arbs = get_arbs(best_odds)
            except Exception as failed_getting_arbs:
                logging.error(f'Failed getting arbs: {failed_getting_arbs}')

            market_details.append({
                "sport":  sport_key,
                "sportTitle":  sport_title,
                "commencement":  commence_time,
                "homeTeam":  home_team,
                "awayTeam":  away_team,
                "liveMatch": odds_offered_time > commence_time,
                "odds": match_market,
                "bestOdds": best_odds,
                "arbitrage": arbs
            })

    return market_details


# Function to find best odds and associated bookmaker
def find_best_odds(
        data: dict
    ) -> tuple:
    """
    This function filters through all odds for a given sport and returns 
    the best odds and current arbitrage opportunities in the market, including lay arbitrage.
    """

    arbitrage_opportunities = []
    best_bets = []
    for event in data:
        event_best_odds = {}
        event_best_lays_odds = {}
        commence_time = event['commence_time']
        sport_title = event['sport_title']
        
        # Iterate through bookmakers and extract back and lay odds
        for bookmaker in event['bookmakers']:
            bookmaker_name = bookmaker['title']
            if bookmaker_name:
                for market in bookmaker['markets']:
                    # Extract back odds (H2H)
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            name = outcome['name']
                            price = outcome['price']
                            # Update the best back odds
                            if name not in event_best_odds or price > event_best_odds[name]['price']:
                                event_best_odds[name] = {
                                    'price': price,
                                    'impliedLikelihood': 1/price,
                                    'bookmakerName': bookmaker_name
                                }
                    
                    # Extract lay odds (H2H Lay)
                    if market['key'] == 'h2h_lay':
                        for outcome in market['outcomes']:
                            name = outcome['name']
                            price = outcome['price']
                            # Update the best lay odds
                            if name not in event_best_lays_odds or price < event_best_lays_odds[name]['price']:
                                event_best_lays_odds[name] = {
                                    'price': price,
                                    'impliedLikelihood': 1/price,
                                    'bookmakerName': bookmaker_name
                                }
        
        # Check for standard arbitrage opportunities (back odds)
        total_odds = sum(event_best_odds[team]['impliedLikelihood'] for team in event_best_odds)
        
        if total_odds < 1:
            arbitrage_opportunities.append({
                'sportTitle': sport_title,
                'commenceTime': commence_time,
                'payOut': total_odds,
                'bestOdds': event_best_odds,
                'type': 'Back Arb'
            })

        # Check for lay arbitrage opportunities (comparing back vs lay odds)
        for team in event_best_odds:
            if team in event_best_lays_odds:
                back_odds = event_best_odds[team]['price']
                lay_odds = event_best_lays_odds[team]['price']

                # Lay arbitrage if the lay odds provide a lower implied likelihood
                if lay_odds < back_odds:
                    arbitrage_opportunities.append({
                        'sportTitle': sport_title,
                        'commenceTime': commence_time,
                        'backOdds': event_best_odds[team],
                        'layOdds': event_best_lays_odds[team],
                        'team': team,
                        'type': 'Lay Arb'
                    })
        
        best_bets.append({
            'sportTitle': sport_title,
            'commenceTime': commence_time,
            'bestOdds': event_best_odds,
            'bestLayOdds': event_best_lays_odds
        })

    return arbitrage_opportunities, best_bets