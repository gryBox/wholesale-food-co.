def on_session_created(session_context):
	setattr(session_context._document,'dfDict',session_context.server_context.dfDict)