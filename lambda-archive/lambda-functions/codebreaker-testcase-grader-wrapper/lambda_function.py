import os
import json
import boto3
import uuid
from decimal import *

judgeName = os.environ['judgeName']
region = os.environ['AWS_REGION']
client = boto3.client('sts') 
accountId = client.get_caller_identity()['Account'] # Gets account Id programatically

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
submissions_table = dynamodb.Table(f'{judgeName}-submissions')

def lambda_handler(event, context):
    submissionHash = uuid.uuid4()
    subId = event["submissionId"]
    testcaseNumber = event["testcaseNumber"]
    MLE = float(event["memoryLimit"])
    language = event["language"]
    
    response = None
    if MLE <= 1024:
        response = lambda_client.invoke(
            FunctionName = f'arn:aws:lambda:{region}:{accountId}:function:codebreaker-testcase-grader',
            InvocationType='RequestResponse',
            Payload = json.dumps(event)
        )
    else:
        response = lambda_client.invoke(
            FunctionName = f'arn:aws:lambda:{region}:{accountId}:function:codebreaker-testcase-grader-2048',
            InvocationType='RequestResponse',
            Payload = json.dumps(event)
        )
        
    result = json.loads(response['Payload'].read())

    result['score'] = Decimal(str(result['score']))
    response = submissions_table.update_item(
        Key = {'subId' : subId},
        UpdateExpression = f'set verdicts[{testcaseNumber}] = :verdict, times[{testcaseNumber}] = :time, memories[{testcaseNumber}]=:memory,score[{testcaseNumber}]=:score,returnCodes[{testcaseNumber}]=:returnCode,#st [{testcaseNumber}]=:status',
        ExpressionAttributeValues = {':verdict':result['verdict'],':time':Decimal(str(result['runtime'])), ':memory':Decimal(str(result['memory'])), ':score':result['score'], ':returnCode':result['returnCode'],':status':2},
        ExpressionAttributeNames = {'#st':'status'}
    )
    
    return result
