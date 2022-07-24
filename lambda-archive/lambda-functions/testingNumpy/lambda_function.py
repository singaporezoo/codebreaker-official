import json
import subprocess
import numpy # This line runs

def lambda_handler(event, context):
    try:
        # proc = subprocess.run("pip3 install numpy; python3 test.py", shell=True, capture_output=True) # This doesn't
        proc = subprocess.run("pwd", shell=True, capture_output=True)
        print(proc.stdout)
        print(proc.stderr)
    except Exception as e:
        print(e)
        
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
