from bokeh.server.server import Server
from bokeh.command.util import build_single_handler_applications
from bokeh.embed import autoload_server
from flask import Flask,render_template, redirect, url_for, request,session
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.autoreload
import sys
from collections import OrderedDict
import threading
import time
import pandas as pd
from datetime import datetime
import os
this_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(this_path)
import live_data
from functools import wraps,partial
import signal
from clean_dfs import clean_dfs
class BigServer(object):

	def setup_bokeh(self):
		##turn file paths into bokeh apps
		apps = build_single_handler_applications(self.app_path_dict.keys(),self.app_path_dict)
		
		##kwargs lifted from bokeh serve call to Server, with the addition of my own io_loop
		kwargs = {
			'io_loop':self.io_loop,
			'generade_session_ids':True,
			'redirect_root':True,
			'use_x_headers':False,
			'secret_key':None,
			'num_procs':1,
			'host':['%s:%d'%(self.host,self.app_port),'%s:%d'%(self.host,self.bokeh_port)],
			'sign_sessions':False,
			'develop':False,
			'port':self.bokeh_port,
			'use_index':True
		}
		#instantiate the bokeh server
		srv = Server(apps,**kwargs)

		#return bokes object
		return srv

	def setup_flask(self):
		#instantiate flask, and set the encryption
		self.flask_app = Flask(__name__)
		self.flask_app.config["SECRET_KEY"] = "6578df48serg486w3434n0w34$$$$aaaaaewfwef$$$$$$$61we5b,90w4ve,07345pbn32v7$$$$$$$$5w43nwe57w34y66w4h86webm9$$$$$$$$086v78e..as...$$$$$$$$$$$$$;9pwvm;m,zF>)>)#WF>)_$W$FT&"

		@self.flask_app.route('/graphs',methods=['GET']) # Our current working home page. contains all of the tabs with the graphs.
		def graph_page():
			# grab the bokeh divs from the bokeh server
			bokeh_scripts = {} 
			for plot in self.app_names:
				#A fail safe to avoid loading an empty plot
				try:
					bokeh_scripts[plot]=autoload_server(model=None, url='http://%s:%d'%(self.host,self.bokeh_port), app_path="/"+plot) # pulls the bokeh apps off of the bokeh server
				except Exception as e:
					print(plot+' could not be loaded because: ')
					print(e)
			other_divs ={}     
			for i in self.embedable_divs:
				f = open(os.path.join(this_path,'other_pages',i),'r')
				i=i.replace('.','_')
				other_divs[i]=f.read()
				f.close() 

			# Insert the bokeh documents into the tabs on the jinja template
			all_divs= OrderedDict()  ##combine the two dicts
			all_divs.update(bokeh_scripts)
			all_divs.update(other_divs)
			all_divs = OrderedDict(sorted(all_divs.items(), key=lambda x: x[0]))
			
			return render_template('graph_template.html',div_dict=all_divs)
		
		#a catchall for any bad urls
		@self.flask_app.route('/', defaults={'path': ''})
		@self.flask_app.route('/<path:path>')
		def catch_all(path):                       
			return redirect(url_for('graph_page'))

		
	def insert_data(self,in_dict):
		#avoid race conditions, a mutex of sorts
		while self.insert_running:
			time.sleep(1)
		self.insert_running = True

		#add the new data to the main dictionary
		self.df_dict.update(in_dict)

		#clean the new data and add it to the clean dictionary
		self.clean_dict.update(clean_dfs(in_dict,bokeh_dir = self.app_path))

		#checks to see if the bokeh server has been instantiated already
		try:
			self.bokeh_server
		except AttributeError:
			self.insert_running = False
			return

		#loops through the app contexts in bokeh
		for app_name,app_context in self.bokeh_server._tornado._applications.items():

			#adds the appropriate data to the appropriate document
			setattr(app_context._server_context,'dfDict',self.clean_dict[app_name.replace('/','')])

			#loops through every live session
			for k,ses in app_context._sessions.items():
				#updates the df dict that session has
				ses._document.dfDict.update(self.clean_dict[app_name.replace('/','')])
				
				#calls that documents update_callback with a next tick callback
				if hasattr(ses._document,'update_callback'):
					ses._document.add_next_tick_callback(partial(ses._document.update_callback))
		self.insert_running = False

	#functionality to catch ctrl-c and shut down cleanly
	def catch_interrupt(self,signum,frame):
		print('caught an interrupt')
		self.close_it = True
	
	def try_closing(self):
		if self.close_it:
			self.io_loop.stop()
			print('server shut down sucessfull')
			sys.exit(0)
	
	#polls live data to see if it has anything new for me
	def listen_for_live(self):
		while True:
			if self.ldl.has_new_data:
				self.insert_data(self.ldl.get_data())
			time.sleep(1)

	def start_server(self,host='localhost', app_port=9876,bok_port=5006):

		#initialize the server settings, maybe the defaults should come from a config?
		self.bokeh_port = bok_port
		self.app_port=app_port
		self.host = host
		
		#initailize the flask app		 
		self.setup_flask()
		#glue the the flask_app to the tornado server
		http_server = tornado.httpserver.HTTPServer(
			tornado.wsgi.WSGIContainer(self.flask_app)
		)

		#start the server list
		http_server.listen(self.app_port)
		self.io_loop = tornado.ioloop.IOLoop.instance()
		
		#initialize the bokeh server
		self.bokeh_server = self.setup_bokeh()

		#stick the dictionary of dataframes to each bokeh applications application_context, so it can be pulled by the bokeh docs
		for key,app_context in self.bokeh_server._tornado._applications.items():
			app_context.server_context
			try:
				setattr(app_context._server_context,'dfDict',self.clean_dict[key.replace('/','')])
			except KeyError:
				pass

		#add a handler for catching ctrl-C event and closing cleanly
		signal.signal(signal.SIGINT, self.catch_interrupt)
		tornado.ioloop.PeriodicCallback(self.try_closing,100).start()

		#start a thread to listen for live data
		live_thread = threading.Thread(target=self.listen_for_live)
		live_thread.start()

		#print some debugs
		print(datetime.now())
		#called here with an empty dict so that the current clean_dict is passed to the bokeh application_contexts
		#this is called because insert_data breaks if it's called before bokeh server has been instantiated
		self.insert_data({})

		print('starting server on %s:%d'%(host,app_port))
		self.io_loop.start()

			#TODO: add close down email
	def __init__(self,init_dfs):

		#initialization
		self.app_path = this_path+'\\bokeh_plots\\'#a little hard coded, but I'm over it
		self.app_names = os.listdir(self.app_path)#finds the name of all of the dirs in the bokeh directory	
		self.close_it = False#boolean used to shut down cleanly on ctrl-c event
		self.df_dict = {}#dict containing all existing dfs
		self.clean_dict = {}#dict containing dfs that've been passed through the cleaning functions
		self.insert_running = False #boolean used as a mutex by insert data
		self.ldl = live_data.live_data_loader()#instantiate the live data loader class
		self.insert_data(self.ldl.get_data())#insert the initial data from the live files
		self.insert_data(init_dfs)#insert the data passed on init
		self.embedable_divs = os.listdir(os.path.join(this_path,'other_pages\\'))
		#a little magic to make bokeh server work right
		self.app_path_dict = {}
		for app in self.app_names:
			self.app_path_dict[self.app_path+app] = None
		