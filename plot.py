import json
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

with open("historical.json", "r") as f:
    d = json.load(f)

# convert json to dataframe and reset index
df = pd.DataFrame(d)
df = df.reset_index()

# print(df.to_numpy())

cols = df.shape[1]
rows = df.shape[0]

for i in range(5,6):
    data = []

    for j in range(rows):
        if i > 0: # column 0 stores date and time only
            data.append(df[i][j])
            print(df[i][j])
    
    data = pd.DataFrame(data, columns=['pool_name','daily_volume'])
    data['daily_volume']=data['daily_volume'].astype(float)
    data.plot(use_index=True)
    data.plot(y='daily_volume')
    
    plt.suptitle('Daily Volume for BUSD Pool')
    #plt.savefig("Graph_BUSD_Pool")
    plt.close()