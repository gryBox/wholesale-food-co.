import pandas as pd
import threading
import time
import os
import io
from configparser import ConfigParser

class live_data_loader(object):
	
	#reads either csvs or xl files, more will probably be added later
	def readit(self,path):

		#pull the suffix out of the path. The dollar sign is used to delimit file path and sheet name for xl type files
		suffix = path.split('.')[-1].split('$')[0]
		if(suffix=='csv'):
			df=pd.read_csv(path)
		elif('xl' in suffix):#could be xlsm xls xlxs gets all of those and puts its faith in pandas
			xlParts = path.split('$')
			df=pd.read_excel(xlParts[0],xlParts[1])

		return df

	#a thread to watch a file, and set a flag when new data is found
	def live_data_thread(self,key,file_path,frequency=1):
		#get the initial modify time of the file
		old_time = os.path.getmtime(file_path.split('$')[0])

		#go into an infinate loop
		while(True):
			#checks to see if the the file has been updated
			try:
				if os.path.getmtime(file_path.split('$')[0]) != old_time:
					old_time = os.path.getmtime(file_path.split('$')[0])#updates old_time to avoid looping
					self.data[key] = self.readit(file_path)#adds the new data to the big data dict
					self.has_new_data = True#sets the flag
			except Exception as e:#catch all errors, keep thread alive
				print(e)
				pass
			time.sleep(frequency)#sleeps to avoid blowing up the cpu
	def get_data(self):
		#return the data and set the flag
		self.has_new_data=False
		return self.data

	def __init__(self,frequency=1):
		self.data = {}
		threads = []
		self.has_new_data = False

		#reads the config file and gets the locations of the files to watch
		cp = ConfigParser()
		cp.read(os.path.dirname(os.path.abspath(__file__))+'\\data_locations.ini')

		#does one initial read so the server can grab the data initially
		for key,path in cp['LIVE'].items():
			self.data[key]=self.readit(os.path.dirname(os.path.abspath(__file__))+'\\..\\'+path)
			self.has_new_data = True
		#starts the threads to watch the server
		for key,path in cp['LIVE'].items():	
			threads.append(threading.Thread(target=self.live_data_thread,args=(key,os.path.dirname(os.path.abspath(__file__))+'\\..\\'+path,frequency)))
			threads[-1].start()