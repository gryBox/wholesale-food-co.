from bokeh.io import curdoc
from bokeh.models import ColumnDataSource,HBox
from bokeh.models.widgets import DataTable,TableColumn,StringFormatter,NumberFormatter
from tornado.gen import coroutine

#standard bokeh datatable setup, "dfDict" is a dictionary of dataframes that has been attached to this document by the server
data = ColumnDataSource.from_df(curdoc().dfDict['prices'])
source = ColumnDataSource(data = data)
columns = [
	TableColumn(field = 'FRUIT',title='Fruit',width=250,formatter=StringFormatter(text_align='center')),
	TableColumn(field = 'CURRENT_PRICE',title = 'Current Price',width=250,formatter = NumberFormatter(format='$0,0.00')),
	TableColumn(field = 'IN_SEASON',title='In Season',width=150,formatter=StringFormatter(text_align='center'))
]
data_table = DataTable(source=source, columns=columns, width=600, height=280,fit_columns=False,row_headers=False)

#a function callable from a different thread to update the data
@coroutine
def update_table():
	source.data = ColumnDataSource.from_df(curdoc().dfDict['prices'])

#I put the update function in a place the server can call whenever new data arrives. By doing this, I am able to
#have only have one thread looking for live data, as opposed to having a new periodic_callback for every session
#that gets opened.
curdoc().update_callback = update_table

#standard bokeh
curdoc().add_root(HBox(data_table))
curdoc().title = 'Fruit Market'