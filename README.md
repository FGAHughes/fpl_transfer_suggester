This is a program that predicts fantasy football players (referred to in program as elements) points and recommends transfers each gameweek, tailored to your team.

Required libraries: Requests, Numpy, Pandas

To use the program, open main.py and input the parameters into 'run_fpl_script'. The first parameter, 'gw_comparison' should be the number of gameweeks you would like the algorithm to predict the best players to bring in for. The second, 'force_update', should only be True or False, and this will depend on whether you want the algorithm to update its data at the point of running. The algorithm automatically updates every 12 hours or after each finished fixture. The final parameter is the managerID of the fpl manager that you want the function to suggest transfers for. You can find a managerID by logging into the FPL website, navigating to 'Points' and finding the ID in the url, like so 'fantasy.premierleague.com/entry/{The ID will be here}/event/gameweek'.

Alternatively, you can open element_master.csv to see player's predicted points. These will be ranked by whichever gameweek range I had inputted into the algorithm last so be wary of that.

The algorithm will create a series of dataframes to help with transfer decisions. These include suggested transfers, every player ranked by predicted points in gw_comparison, each team's attacking and defensive data and a suggested starting xi.

Some limitations of the algorithm include:
- Affordable transfers are calculated by players absolute prices. For example, if you bought a player for 5.0, and they are now worth 5.4, their value to you will be 5.2 but the algorithm may suggest players 5.4 (in addition to what is available in your bank). 
- The algorithm calculates predicted points based off of the players' and teams' performances in their last 9 fixtures by default. From my experience 7-9 gameweeks works best but this has not been objectively tested. The gameweek range can be edited in code.
