'''
Purpose: Data Visualization on Historical Option Volatility in FQ space
'''

import copy
from collections import OrderedDict
import sys
import os
from seaborn import SEABORN_PALETTES
import pandas as pd
from bokeh.plotting import figure,curdoc
from bokeh.models import HBox, TapTool,VBox,HoverTool, WidgetBox, WheelZoomTool, SaveTool, PanTool, Legend,BoxZoomTool,DataRange1d,CustomJS
from bokeh.models.widgets import Slider, TextInput, Select,Button, RadioButtonGroup, PreText, Paragraph, CheckboxGroup,Div,Toggle
from pandas.tseries.offsets import *
from datetime import datetime,timedelta,date
import time

#grab the lev utils from a relative file path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..\\..\\..\\'))
from example_utils.math_utils import math_utils as mu

import numpy as np
############HELPER FUNCTIONS

#converting a timestamp to an epoch with a start of 1970
def ts_to_epoch(timestamp):
	if type(timestamp) == type(1):
		return timestamp

	elif type(timestamp) == np.datetime64:
		timestamp = timestamp.astype('uint64')
		return timestamp/1000000
	else:
		return (timestamp - datetime(1970,1,1)).total_seconds()*1000

#calculates the outer ranges of the graph, then adds an approptiate amount of padding to the 
def calc_range(lines):
	xmin = float(999999999999999999)
	xmax = float(-1)
	ymin= float(999999999999) 
	ymax = float(-1)
	for i in lines:
		if i.glyph.visible:
			if ts_to_epoch(min(i.data_source.data['x'])) <xmin:
				xmin =  ts_to_epoch(min(i.data_source.data['x']))
			if  ts_to_epoch(max(i.data_source.data['x'])) >xmax:
				xmax = ts_to_epoch(max(i.data_source.data['x']))
			if min(i.data_source.data['y']) <ymin:
				ymin =  min(i.data_source.data['y'])
			if max(i.data_source.data['y']) >ymax:
				ymax = max(i.data_source.data['y'])
	pad = 0.05
	xpad = (xmax-xmin)*pad
	ypad = (ymax-ymin)*pad
	return xmin-xpad,xmax+xpad,ymin-ypad,ymax+ypad


#grabs a copy of the potential options for Asset_Class, Product, and From
ddOpts = curdoc().dfDict['ddOpts']
fruit_df = curdoc().dfDict['fd_full']
file_counter=0
#the dataframe containing stats on each line
descDf = None
in_click = False

#formats the pandas output
pd.set_option('display.max_colwidth',1000)
def buildPlot():
	#####################Setup
	# Grab graph colors, pop undesireable ones
	colors = SEABORN_PALETTES['bright']

	#Grab and sort the FQs
	quals = fruit_df.reset_index()
	quals = quals['FruitQuality'].unique().tolist()
	for idx, i in enumerate(list(quals)):
	    if type(i) == type(0.5):
	        quals.pop(idx)
	unique_FQs = quals
	
	#a little math to get the epoch time to set the initial x range	
	minDate =ts_to_epoch(fruit_df['Date'].min())
	maxDate = ts_to_epoch(fruit_df['Date'].max())

	###########Create and format the plot
	plot = figure(
		x_axis_type="datetime", 
		plot_width=600, 
		plot_height=400,
		tools=[PanTool(),WheelZoomTool(),SaveTool(),BoxZoomTool()],		
		x_range = DataRange1d(start=minDate,end=maxDate), #sets the initial date range  to the limits of the data
		y_range = DataRange1d(start=0,end=1),
		name = 'the_plot',
		toolbar_location = 'above')
	#some styling
	plot.title.text = "Historical Volatility"
	plot.xaxis.axis_label="Trade Date"
	plot.yaxis.axis_label="Vol"
	plot.background_fill_color='#EAEBF0'
	plot.xgrid.grid_line_color = 'white'
	plot.ygrid.grid_line_color = 'white'
	plot.xaxis.axis_line_color = 'white'
	plot.xaxis.major_tick_line_color = 'white'
	plot.xaxis.minor_tick_line_color = 'white'
	plot.yaxis.axis_line_color = 'white'
	plot.yaxis.major_tick_line_color = 'white'
	plot.yaxis.minor_tick_line_color = 'white'
	plot.toolbar.logo = None
                                                 
	#a list for all of the lines to reside in
	lines = [] 
	legends = []

	##############Create the widgets

	#a console style window to show debug messages TODO: add on/off functionality
	debug = PreText(text="",width=1200,height=500) 
	
	#echos the debug in a place more visiable for the user
	user_message = Paragraph(text='')
	

	
	#Asset_Class, Product, and From dropdown boxes. Sets dropdown's initial value.
	asCls = Select(title="Asset Class",options=ddOpts['Asset_Class'].unique().tolist())
	asCls.value =asCls.options[0]
	prod = Select(title="Products",options=ddOpts[ddOpts['Asset_Class']==asCls.value]['Product'].unique().tolist())
	prod.value =prod.options[0]
	whereFrom=Select(title="From",options=ddOpts[(ddOpts['Asset_Class']==asCls.value) & (ddOpts['Product']==prod.value)]['From'].unique().tolist())
	whereFrom.value = whereFrom.options[0]
	FQslider = Slider(title='Fruit Quality',start = min(unique_FQs),end = max(unique_FQs), step = 1)
	
	#the amount of days back to look for the data
	days_back = TextInput(title='Days ago',value='365')
	days_back_buttons = RadioButtonGroup(labels=['10','30','90','180','365','730'],active=4)
	
	#the date to linear fit to
	fixed_date_buttons = RadioButtonGroup(labels=['30','60','90','120','180','365'],active=2)
	fixed_date = TextInput(title = 'Days to Exp',value='90')	
	
	#the amount of days with which to calculate the rolling mean
	rolling_days_buttons = RadioButtonGroup(labels=['1','2','5','10'],active=0)
	rolling_days = TextInput(title = 'Rolling Mean Days',value='1')
	
	#a dynamically resizing checkbox group that allows for the changing of the visablity of any line on the plot
	line_onOff = CheckboxGroup(width=400,name='line_onOff')
	
	#the associated colors to act as a legend for line_onOff
	legendDiv = Div(width = 50)

	#button to add a line
	addLine = Button(label = "Add Line")
	
	#an html rendered visualization of the data for each line
	descriptions = Div(text='',width=500)



	#resizes the plot
	rszButton=Button(label='resize')
	##########Define functions associated with the widgets
	
	#concats any dubug call to the end of the current debug text, and changes the user message
	def updateDebug(inString):
		inString = str(inString)
		user_message.text = inString
		oldText = debug.text
		newText = ("*- "+str(datetime.now())+" : "+inString)
		debug.text=oldText+'\n'+newText
	
	#changes the potential products and contract categories to match the user selected asset class
	def asClsChange(attrname,old,new):
		prod.options=ddOpts[ddOpts['Asset_Class']==asCls.value]['Product'].unique().tolist()
		prod.value = prod.options[0]

	#changes the potential contract categories to match the user selected product
	def prodChange(attrname,old,new):
	    whereFrom.options=ddOpts[(ddOpts['Asset_Class']==asCls.value) & (ddOpts['Product']==prod.value)]['From'].unique().tolist()
	    whereFrom.value=whereFrom.options[0]

	#links the days back button and text box
	def days_back_buttonChange(attrname,old,new):
		days_back.value=days_back_buttons.labels[days_back_buttons.active]

	#checks that the users input is an int
	def days_backChange(attrname,old,new):
		try:
			days_back.value = str(int(days_back.value))
		except ValueError:
			days_back.value = '0'
			updateDebug('please type an integer')

	#links the fixed date button and text box
	def fixed_date_buttonChange(attrname,old,new):
		fixed_date.value = fixed_date_buttons.labels[fixed_date_buttons.active]

	#checks that the users input is an int
	def fixed_dateChange(attrname,old,new):
		try:
			fixed_date.value= str(int(fixed_date.value))
		except ValueError:
			fixed_date.value = '0'
			updateDebug('please type an integer')

	#links the rolling days button and text box
	def rolling_days_buttonsChange(attrname,old,new):
		rolling_days.value = rolling_days_buttons.labels[rolling_days_buttons.active]

	#checks that the users input is an int
	def rolling_daysChange(attrname,old,new):
		try:
			rolling_days.value = str(int(rolling_days.value))
		except ValueError:
			rolling_days.value = '0'
			updateDebug('please type an integer')


	#fits the plot to the currently visiable lines
	def resize():
		if len(line_onOff.active) == 0 or len(line_onOff.labels)==0:

			plot.x_range.start = ts_to_epoch(fruit_df['Date'].min())
			plot.x_range.end = ts_to_epoch(fruit_df['Date'].max())
			plot.y_range.start = 0
			plot.y_range.end =  100
		else:
			xmin,xmax,ymin,ymax = calc_range(lines)
			plot.x_range.start = xmin
			plot.x_range.end = xmax
			plot.y_range.start = ymin
			plot.y_range.end = ymax



	#turn lines on or off 
	def line_onOffChange(attrname,old,new):
		for i in range(len(line_onOff.labels)):
			if i in line_onOff.active:
				lines[i].glyph.visible = True
			else:
				lines[i].glyph.visible= False
		legendDiv.text = '<div>'
		for line in lines:
			legendDiv.text+='<br><div style="background-color: %s; float:up; padding: 4px 4px 4px 4px"></div><br>'%line.glyph.line_color
		legendDiv.text+='</div>'
		resize()


	#adds a line to the graph
	def grphUpdt():
		#adds some debug messages, grabs the current time as to later show the total time taken to calculate
		updateDebug("Starting")
		updateDebug("total dataframe size: " + str(fruit_df.shape))
		stTime = datetime.now()

		#the value to linear fit to
		fit_to = int(fixed_date.value)


		#instiantiate an empty dataframe that will eventually contain the graphs data
		graphData = pd.DataFrame({'Date':[],'PriceVolatility':[],'Days_to_Exp':[]})
		

		#grab the appropriate subset of the whole dataframe based on the users input into the widgets
		updateDebug("querying the data..")

		try:
			workingDf=fruit_df.loc[asCls.value,prod.value,whereFrom.value]
		except KeyError:
			updateDebug('no data with that combination of Asset Class, Product, From')
			return

		try:
			workingDf = workingDf[['Date','PriceVolatility','Days_to_Exp']][(workingDf['Date']>(date.today() - timedelta(days=int(days_back.value))))]
		except KeyError:
			updateDebug('no data with that combination of Asset Class, Product, From, and days back')
			return
		updateDebug("done breaking down df")

		#a hook in the case that the users inputs resulted in an empty dataframe
		if(workingDf.empty):
			updateDebug('no data with that combination of Asset Class, Product, From, and days back')
			return


		#widdle down the database to only contain the user specified FQ
		try:
			graphData = workingDf.loc[int(FQslider.value)].copy()
		except KeyError:
			updateDebug('no data with that FQ')

		#another empty graph hook
		if(graphData.empty):
			updateDebug('no data with that combination of Asset Class, Product, Contract Category, FQ, and days back')
			return
		updateDebug('grabed correct FQs')

		#calculate linear fit on the current subset
		updateDebug('calculating linear fit...')
		graphData = mu.linearFit(fit_to=fit_to,group_on_column='Date',df=graphData,fit_column='Days_to_Exp',on_columns=['PriceVolatility'])
		updateDebug('finished with linear fit')

		# a few more debug messages
		updateDebug("working df qry: Asset_Class = %s and Product = %s and From = %s and Date > %s " % (asCls.value,prod.value,whereFrom.value, str(date.today() - timedelta(days=int(days_back.value)))))
		updateDebug("graph data shape: "+str(workingDf.shape))

		#makes sure graph data has at least 5 rows, so that rolling mean can be calculated
		if graphData.shape[0]>int(rolling_days.value):
			
			#make the graph legend, based on if there's a denominator specified or not
			this_legend = '%s - %s FQ: %s Days to Exp: %s From: %s Rolling Days: %s' % (prod.value,whereFrom.value,int(FQslider.value),fixed_date.value,str(date.today() - timedelta(days=int(days_back.value))),rolling_days.value)



			
			#add a new line to the graph, and add the accosiated GlyphRenderer created by adding the line to the lines list. 
			#Set the legend to the previously calculated legend, and set the color to the next color in the current theme (if there are more lines than colors, there will be multiple lines with the same color)
			#Calculates a 5 day rolling mean on the y values. Maybe add a slider/text box/other widget so the user can set the rolling mean themselves
			updateDebug('adding line to plot')
			lines.append(
				plot.line(graphData.index.values[int(rolling_days.value)-1:],
				graphData['PriceVolatility'].rolling(window=int(rolling_days.value)).mean()[int(rolling_days.value)-1:], 
				line_width = 3, 
				color=colors[len(lines)%len(colors)]
				)
			)
			legends.append(this_legend)
			updateDebug("updated graph")
			
			global descDf

			#either creates, or adds to, a dataframe containing statistics about the data. stats come from pandas DataFrame.describe. 
			if descDf is None:
				graphData[this_legend] = graphData['PriceVolatility']
				descDf = graphData[[this_legend]].rolling(window=int(rolling_days.value)).mean()[int(rolling_days.value)-1:].describe(percentiles=[]).transpose().copy()
			else:
				graphData[this_legend] = graphData['PriceVolatility']
				descDf = pd.concat([descDf,graphData[[this_legend]].rolling(window=int(rolling_days.value)).mean()[int(rolling_days.value)-1:].describe(percentiles=[]).transpose().copy()])
			
			descDf = descDf.round(1)
			descriptions.text = descDf.to_html().replace('\\n','')
			graphData.drop(this_legend,1,inplace=True)

			#add the name of the line to the checkbox so that it can be turned off and o
			line_onOff.labels.append(this_legend)
			line_onOff.active.append(len(line_onOff.labels)-1)
			legendDiv.text = '<div>'
			for line in lines:
				legendDiv.text+='<br><div style="background-color: %s; float:up; padding: 4px 4px 4px 4px"></div><br>'%line.glyph.line_color
			legendDiv.text+='</div>'
			##leaving this in case we get around to figuring out the hover tool
			##formats the date values for the hover tool, currently commented out until we, or bokeh, fix the hover tool for multiple lines
			#formDates= pd.to_datetime(graphData['Date'] ,format="%m-%d-%Y")
			#lines[-1].data_source.data['formDates'] = formDates.apply(lambda x: x.strftime('%m-%d-%Y'))
			
			##Displays the amout of time it took to draw the line, as well as the number of points in the graph
			updateDebug("updated y vals, with rolling mean calculated")
			updateDebug(str(datetime.now()-stTime) +" FOR "+str(len(lines[-1].data_source.data['x'])) +" points")
		else:
			updateDebug("There's no data to display")
		del graphData
		del workingDf

	#######Link widgets to their associated functions 
	asCls.on_change('value',asClsChange)
	prod.on_change('value',prodChange)
	days_back_buttons.on_change('active',days_back_buttonChange)
	days_back.on_change('value',days_backChange)
	fixed_date_buttons.on_change('active',fixed_date_buttonChange)
	fixed_date.on_change('value',fixed_dateChange)
	rolling_days_buttons.on_change('active',rolling_days_buttonsChange)
	rolling_days.on_change('value',rolling_daysChange)
	line_onOff.on_change('active',line_onOffChange)
	addLine.on_click(grphUpdt)
	rszButton.on_click(resize)


	#Formatting 
	fixed_date_box = WidgetBox(fixed_date,fixed_date_buttons)
	days_back_box = WidgetBox(days_back,days_back_buttons)
	rolling_days_box = WidgetBox(rolling_days,rolling_days_buttons)
	widgets=[asCls,prod,whereFrom,FQslider,days_back_box,fixed_date_box,rolling_days_box,addLine,rszButton,user_message]
	plot_w_description = VBox(plot,descriptions,width=700)
	pwd_w_leg = HBox(plot_w_description,VBox(legendDiv),VBox(line_onOff),width=plot_w_description.width+line_onOff.width+100,name = 'div_to_save')
	input_box = VBox(*widgets,width=400,height=1200)
	total_box = HBox(VBox(input_box),VBox(pwd_w_leg),width=input_box.width+pwd_w_leg.width+100,height=1200)
	tot_w_debug =VBox(total_box,VBox(HBox(debug)))

	resize()
	return tot_w_debug

#calls the method to build the plot then adds it to the document
doc_box= buildPlot()
curdoc().add_root(doc_box)
curdoc().title = 'Fruit Market'