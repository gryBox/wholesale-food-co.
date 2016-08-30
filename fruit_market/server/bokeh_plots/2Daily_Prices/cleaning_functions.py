import pandas as pd
import datetime
from collections import namedtuple
class dataframe_cleaner(object):


	Mapping = namedtuple('Mapping',['in_df','out_df','func'])
	#I simply need to pass my data, don't need to clean it in any way
	def move_along(df):
		return df

	df_func_map=[
		Mapping(in_df='today_price',out_df='prices',func = move_along)
		]
