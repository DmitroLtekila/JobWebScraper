import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json

def plot_technology_frequency():
    with open('top_technologies.json', 'r') as file:
        json_data = json.load(file)
    df = pd.DataFrame(list(json_data.items()), columns=["Technology", "Frequency"])
    df.plot(kind='area', x='Technology', y='Frequency')
    plt.ylabel('Frequency')
    plt.show()
    
    # to many variables for a pie chart, so it's not the most convenient way to visualize the data
    # y = list(json_data.values())
    # x = list(json_data.keys())
    # plt.pie(y, labels=x, autopct='%1.1f%%')
    # plt.show()

if __name__=="__main__":
    plot_technology_frequency()