import pandas as pd
import matplotlib.pyplot as plt
import json

def plot_technology_frequency():
    with open('top_technologies.json', 'r') as file:
        json_data = json.load(file)
        print(json.dumps(json_data, indent=4))

if __name__=="__main__":
    plot_technology_frequency()