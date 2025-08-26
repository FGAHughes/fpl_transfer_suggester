import requests
import pandas as pd

from create_df_funcs import return_main_response, create_element_dfs


mr = return_main_response()

element_master = pd.json_normalize(mr.json(), record_path='elements')
element_master.to_csv('2425_raw_csvs/element_master.csv', index=False)

ids = element_master.id
names = element_master.web_name

for i in range(len(ids)):
    id = ids[i]
    ef, eh = create_element_dfs(id)
    name = names[i]
    eh.to_csv(f'2425_raw_csvs/stats_{name}.csv', index=False)
