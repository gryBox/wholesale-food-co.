import pandas as pd
import sys
import os


def load_data():
	#make this your own to load any data you want initially
	bigDict = {}
	bigDict['fruit_data'] = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),'FruityData.csv'))
	return bigDict
