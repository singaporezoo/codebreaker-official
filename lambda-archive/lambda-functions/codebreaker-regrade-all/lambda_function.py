import json
import time
import awstools

def lambda_handler(event, context):
    
    problemName = event['problemName']
    stitch = event['stitch']
    
    time.sleep(30)
    
    if stitch:
        awstools.updateAllStitchedScores(problemName)
    else:
        awstools.updateAllScores(problemName)
    
    
    return {
        'statusCode': 200
    }
