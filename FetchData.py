# Import libraries
import requests
import pandas as pd

# Define parameters
user_account_id = "YOUR_ACCOUNT_ID" # Replace with your own 32-bit account ID
start_date = "2022-12-01" # Replace with your desired start date
end_date = "2022-12-31" # Replace with your desired end date
patch = "7.30" # Replace with your desired patch version
limit = 10 # Replace with your desired number of results

# Get match history of the user
match_history_url = f"https://api.opendota.com/api/players/{user_account_id}/matches"
match_history_params = {
    "date_min": start_date,
    "date_max": end_date,
    "patch": patch
}
match_history_response = requests.get(match_history_url, params=match_history_params)
match_history_data = match_history_response.json()

# Get match IDs of the user
match_ids = [match["match_id"] for match in match_history_data]

# Get public matches data for those match IDs
public_matches_url = f"https://api.opendota.com/api/publicMatches"
public_matches_params = {
    "less_than_match_id": max(match_ids) + 1 # To get matches before the latest match ID
}
public_matches_response = requests.get(public_matches_url, params=public_matches_params)
public_matches_data = public_matches_response.json()

# Filter public matches data by match IDs and convert to pandas DataFrame
public_matches_df = pd.DataFrame(public_matches_data)
public_matches_df = public_matches_df[public_matches_df["match_id"].isin(match_ids)]

# Get hero names and IDs from OpenDota API
heroes_url = f"https://api.opendota.com/api/heroes"
heroes_response = requests.get(heroes_url)
heroes_data = heroes_response.json()
heroes_dict = {hero["id"]: hero["localized_name"] for hero in heroes_data}

# Define a function to get the win rate of a hero against the user
def get_win_rate(hero_id):
    # Get the matches where the hero was picked or banned
    hero_matches_df = public_matches_df[public_matches_df["picks_bans"].apply(lambda x: hero_id in x)]
    # Count the number of games played and won by the hero against the user
    games_played = len(hero_matches_df)
    games_won = 0
    for index, row in hero_matches_df.iterrows():
        player_slot = row["picks_bans"].index(user_account_id) # Get the player slot of the user (0-9)
        radiant_win = row["radiant_win"] # Get the outcome of the match (True or False)
        if (player_slot < 5 and not radiant_win) or (player_slot >= 5 and radiant_win): # If the user lost the match
            games_won += 1 # Increment the number of games won by the hero against the user
    # Calculate and return the win rate of the hero against the user as a percentage
    win_rate = round(100.0 * games_won / games_played, 2) if games_played > 0 else 0.0
    return win_rate

# Apply the function to all heroes and store the results in a list of tuples
win_rates = [(hero_id, get_win_rate(hero_id)) for hero_id in heroes_dict.keys()]

# Sort the list by win rate in ascending order and get the top N results (limit)
win_rates.sort(key=lambda x: x[1])
top_results = win_rates[:limit]

# Print the results in a table format
print(f"Hero ID\tHero Name\tGames Played\tWins\tWin Rate")
for result in top_results:
    hero_id, win_rate = result # Unpack the tuple into hero ID and win rate
    hero_name = heroes_dict[hero_id] # Get the hero name from the dictionary
    # Get the games played and won by filtering and counting from public matches DataFrame
    games_played = len(public_matches_df[public_matches_df["picks_bans"].apply(lambda x: hero_id in x)])
    games_won = len(public_matches_df[(public_matches_df["picks_bans"].apply(lambda x: hero_id in x)) & ((public_matches_df["picks_bans"].apply(lambda x: x.index(user_account_id))