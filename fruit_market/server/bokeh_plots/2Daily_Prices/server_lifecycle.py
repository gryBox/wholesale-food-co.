#this file is to remain as is. Make sure a copy of this exact file is in your bokeh directory
def on_session_created(session_context):
	setattr(session_context._document,'dfDict',session_context.server_context.dfDict)