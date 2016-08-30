import pandas as pd
import datetime
from collections import namedtuple
class dataframe_cleaner(object):
	Mapping = namedtuple('Mapping',['in_df','out_df','func'])
	def pass_dltspc(df):
		#df = df.pd_df
		df = df.reset_index()
		df = df.set_index(['Asset_Class','Product','From','FruitQuality'])
		df = df.dropna(axis=(0),subset=['Date'])
		df['Date']=pd.to_datetime(df['Date'])
		return df

	def get_ddOpts(df):
		#df = df.pd_df
		df = df.reset_index()[['Asset_Class','Product','From']].drop_duplicates().dropna().copy()
		return df

	df_func_map=[
		Mapping(in_df='fruit_data',out_df='ddOpts',func = get_ddOpts),
		Mapping(in_df='fruit_data',out_df='fd_full',func = pass_dltspc)
		]
