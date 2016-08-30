import importlib.util
import os
def clean_dfs(big_dict,bokeh_dir):
	#get a list of all bokeh directories
	all_dirs = os.listdir(bokeh_dir)
	ret_dict = {}
	
	print('cleaning dfs, this might take a sec')
	#loop through all of the bokeh directories
	for dir_name in all_dirs:
		#load and initialize the cleaning_functions.py. It's like an import, but using a variable filepate
		try:
			spec = importlib.util.spec_from_file_location(
				'dataframe_cleaner',os.path.join(bokeh_dir,dir_name,'cleaning_functions.py')
				)
			Cleaner = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(Cleaner)
			cleaner = Cleaner.dataframe_cleaner()

		#Handles directories without cleaning functions. This allows directories that don't need any initial
		#data to still pass documents to the server
		except Exception as e:
			print(e)
			print('%s has no cleaning_functions.py'%dir_name)
			ret_dict[dir_name] = {}
			continue

		this_dict = {}
		
		#loop through all of the mappers
		for mapper in cleaner.df_func_map:
			try:
				#checks if the input df is a single, or a list
				if type(mapper.in_df) == type([]):
					func_arg = {}

					#adds all of the dfs that the user wants to func_arg
					for df_name in mapper.in_df:
						if df_name not in big_dict.keys():
							print('%s not in the big dictionary'%df_name)
							continue
						func_arg[df_name] = big_dict[df_name]
				else:
					#just set the single
					func_arg = big_dict[mapper.in_df]

				#call the users defined function
				result = mapper.func(func_arg)

				#checks if the user is returning a single, or a list
				if type(mapper.out_df) == type([]):
					for i,key in enumerate(mapper.out_df):
						this_dict[key] = result[i]
				else:
					this_dict[mapper.out_df] = result

			#makes sure one bad cleaning function doesn't disrupt the whole server
			except Exception as e:
				pass



		#adds the dict for this specific user to the total list
		if len(this_dict)>0:
			ret_dict[dir_name] = this_dict
	return ret_dict