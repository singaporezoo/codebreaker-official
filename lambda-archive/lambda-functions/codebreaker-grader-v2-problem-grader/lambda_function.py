import json
import boto3
import datetime
import awstools
from time import sleep
from math import ceil
from concurrent.futures.thread import ThreadPoolExecutor
from boto3.dynamodb.conditions import Key, Attr
import time
dynamodb = boto3.resource('dynamodb')
problems_table = dynamodb.Table('codebreaker-problems')
submissions_table = dynamodb.Table('codebreaker-submissions')
users_table = dynamodb.Table('codebreaker-users')

def lambda_handler(event, context):
    
    problemName = event['problemName']
    submissionId = event['submissionId']
    username = event['username']
    subTime = event['submissionTime']
    language = event['language'] # Language should be from "py" or "cpp"
    stitch = event['stitch']
    regrade = event['regrade']
    regradeall = event['regradeall']
    
    response= problems_table.query(
        KeyConditionExpression = Key('problemName').eq(problemName)
    )
    
    problem_info=response['Items']
    if (len(problem_info) != 1):
        return {
            "statusCode": "300",
            "errorMessage": "No problem found"
        }
    problem_info = problem_info[0]
    timeLimit = problem_info['timeLimit']
    memoryLimit = problem_info['memoryLimit']
    if memoryLimit=="":memoryLimit="256"
    if timeLimit=="":timeLimit="1"
    subtaskDependency = problem_info['subtaskDependency']
    subtaskMaxScores = problem_info['subtaskScores']
    subtaskNumber = len(subtaskDependency)
    testcaseNumber = int(problem_info['testcaseCount'])
    customChecker = problem_info['customChecker']
    
    times = [0 for i in range(testcaseNumber+1)]
    memories = [0 for i in range(testcaseNumber+1)]
    scores = [0 for i in range(testcaseNumber+1)]
    verdicts = [":(" for i in range(testcaseNumber+1)]
    subtaskScores = [0 for i in range(subtaskNumber)]
    returnCodes = [0 for i in range(testcaseNumber+1)]
    status = [1 for i in range(testcaseNumber+1)]
    
    submission_upload = {
         "subId": submissionId,
         "submissionTime": subTime,
         "gradingTime": (datetime.datetime.now()+datetime.timedelta(hours=8)).strftime("%Y-%m-%d %X"),
         "username": username,
         "maxMemory":0,
         "maxTime":0,
         "problemName":problemName,
         "score":scores,
         "verdicts":verdicts,
         "times":times,
         "memories":memories,
         "returnCodes":returnCodes,
         "subtaskScores":subtaskScores,
         "status":status,
         'totalScore':0,
         'language': language
    }
    
    lambda_input = {
        "problemName": problemName,
        "submissionId": submissionId,
        "start": 1,
        "end": testcaseNumber,
        "memoryLimit": float(memoryLimit),
        "timeLimit": float(timeLimit),
        "customChecker": int(customChecker),
        "language": language
    }
    
    awstools.uploadSubmission(submission_upload)
    
    output = {
        'status': 200,
        'payloads': [],
        'username': username,
        'regradeall': regradeall,
        'stitch': stitch,
        'regrade': regrade
    }
    
    for i in range(1, testcaseNumber + 1):
        output['payloads'].append({
            'problemName': problemName,
            'submissionId': submissionId, 
            'testcaseNumber': i,
            'memoryLimit': float(memoryLimit),
            'timeLimit': float(timeLimit),
            'customChecker': int(customChecker),
            'language': language
        })
    
    return output
    