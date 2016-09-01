import sys
import os
this_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(this_path)
from data.load_data import load_data
from server.server import BigServer
import pandas as pd
import time
	
#load all of the static dataframes into one big dictionary
bigDict = load_data()

#instantiate the server, insert the data, then start it up
print('done loading data\nstarting server process')
srv = BigServer(bigDict)
srv.start_server(host='localhost',app_port=6788,bok_port=9878)