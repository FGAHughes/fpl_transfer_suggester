import pandas as pd
import numpy as np

from create_df_funcs import create_element_dfs, return_main_response
from indv_stat_funcs import past_x_performances
from suggest_elements import return_manager_stats


# show all columns and rows
pd.set_option('display.width', None)
pd.set_option('display.max_columns', None)

manager_stats = return_manager_stats(705204, 31)

print(manager_stats[0])


# mr = return_main_response()
# element_master = pd.json_normalize(mr.json(), record_path='elements')
# print(element_master[element_master['id']==159])

# f, s = create_element_dfs(159)
# pxp = past_x_performances(s, 9)
# print(pxp)
#
# rng = np.random.RandomState(1)
# X = 10 * rng.rand(100, 3)
# y = 0.5 + np.dot(X, [1.5, -2., 1.])
# print(y)


