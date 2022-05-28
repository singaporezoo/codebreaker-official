''' 
DOWNLOADS AND UNZIPS ALL LAMBDA FUNCTIONS 

INSTRUCTIONS: EXECUTE FILE IN EMPTY DIRECTORY
'''

import os
import json
from pprint import pprint
import subprocess
import shutil


subprocess.run('rm -rf lambda-functions', shell=True)
process = subprocess.run('aws lambda list-functions', shell=True, capture_output=True)
out = json.loads(process.stdout)
functionNames = [i['FunctionName'] for i in out["Functions"]]

process = subprocess.run('mkdir lambda-functions', shell=True)
for function in functionNames:
	''' GET FILE '''
	process = subprocess.run(f'aws lambda get-function --function-name {function}', shell=True, capture_output=True)
	out = json.loads(process.stdout)
	location = out['Code']['Location']
	subprocess.run(f'wget "{location}" --user-agent="Mozilla"',shell=True)

	files = os.listdir()
	if '.DS_Store' in files: files.remove('.DS_Store') # Just in case mac is annoying
	files.remove('lambda-functions')
	files.remove('get_all_lambda_functions.py')
	# assert len(files) == 1

	''' MOVE INTO FOLDER '''
	filename = f'lambda-functions/{function}.zip'
	subprocess.run(f'mv "{files[0]}" {filename}',shell=True)

	''' UNZIP '''
	shutil.unpack_archive(filename, f'lambda-functions/{function}')
	subprocess.run(f'rm {filename}',shell=True)
