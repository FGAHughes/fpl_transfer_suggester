This is a program that predicts fantasy football players (elements) points and recommends transfers each gameweek, tailored to your team.

To use the program, open main.py and input the parameters into 'run_fpl_script'. The first parameter, 'gw_comparison' should be the number of gameweeks going forward that you want the algorithm to predict the best player to bring in for. The second, 'force_update', should only be True or False, and this will depend on whether you want the algorithm to update it's data at the point of running. The algorithm automatically updates every 12 hours or after each finished fixture. The final parameter is the managerID of the fpl manager that you want the function to suggest transfers for. You can find a managerID by logging into the FPL website, navigating to 'Points' and finding the ID in the url, like so 'fantasy.premierleague.com/entry/{The_ID_will_be_here/event/{current_gameweek}'.

The algorithm will create a series of dataframes to help with transfer decisions. These include suggested transfers, every player ranked by predicted points in gw_comparison, each team's attacking and defensive data and a suggested starting xi.

Some limitations of the algorithm include:
- Not factoring in double or blank gameweeks for predicted points in upcoming fixtures.
- Affordable transfers are calculated by players absolute values. For example, if you bought a player for 5.0 and they are now worth 5.4, their value to you will be 5.2 but the algorithm may suggest players 5.4 in addition to what is available in your bank.