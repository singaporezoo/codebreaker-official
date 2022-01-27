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
    
    response= problems_table.query(
        KeyConditionExpression = Key('problemName').eq(problemName)
    )
    
    problem_info=response['Items']
    if (len(problem_info) != 1):
        return {
            statusCode: "300",
            errorMessage: "No problem found"
        }
    problem_info = problem_info[0]
    print("HELLLOOOO")
    print(problem_info)
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
         "submissionTime": (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %X"),
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
         'totalScore':0
    }
    
    lambda_input = {
        "problemName": problemName,
        "submissionId": submissionId,
        "testcaseNumber": testcaseNumber,
        "memoryLimit": float(memoryLimit),
        "timeLimit": float(timeLimit),
        "customChecker": int(customChecker)
    }
    print(lambda_input)
    awstools.uploadSubmission(submission_upload)
    awstools.gradeSubmission(lambda_input)
    print("Graded!")
    
    graded = 0
    canskip = 1
    jumpLeft = 100
    while jumpLeft > 0:
        # print("Reset ",jumpLeft)
        jumpLeft -= 1
        sleep(0.5)
        response = submissions_table.query(
            KeyConditionExpression = Key('subId').eq(submissionId)
        )
        submission_info = response['Items'][0]
        status = submission_info['status']
        # for i in range(1,len(status)):
            # if(status[i] == 1):
                # print("Fail ",i)
        x = min(status[1:])
        # print(f"X {x}")
        
        if x == 2:
            graded = 1
            break
        elif x == 1 and canskip:
            jumpLeft = 2*(ceil(float(timeLimit)) + 10)
            canskip = 0
    
    # if not graded:
    #     return{
    #         'statusCode':300
    #     }
    response = submissions_table.query(
        KeyConditionExpression = Key('subId').eq(submissionId)
    )
    
    submission_info = response['Items'][0]
    times = submission_info['times']
    memories = submission_info['memories']
    scores = submission_info['score']
    verdicts = submission_info['verdicts']
    status = submission_info['status']
    
    bads = []
    for i in range(1,len(scores)):
        if(status[i] != 2):
            bads.append(i)
    
    for i in bads:
        print(f"Fail {i} time {times[i]}, score {scores[i]}, verdict {verdicts[i]}, status {status[i]}")
    subtaskScores = [100 for i in range(subtaskNumber)]

    maxTime = max(times)
    maxMemory = max(memories)
    
    #Evaluating subtasks
    for i in range(subtaskNumber):
        dep = subtaskDependency[i].split(',')
        for t in dep:
            x = t.split('-')
            if(len(x) == 1):
                ind = int(x[0])
                subtaskScores[i] = min(subtaskScores[i], scores[ind])
            elif len(x) == 2:
                st = int(x[0])
                en = int(x[1])
                for j in range(st,en+1):
                    subtaskScores[i] = min(subtaskScores[i], scores[j])
                    
    
    userinfo = awstools.getUserInfoFromUsername(username)
    problemScores = userinfo['problemScores']
    email = userinfo['email']
     
    totalScore = 0
    for i in range(len(subtaskScores)):
        totalScore += subtaskScores[i] * subtaskMaxScores[i]

    totalScore /= 100
    totalScore = round(totalScore, 2)
    prevScore = 0

    if problemName in problemScores:
        prevScore = problemScores[problemName]

    maxScore = max(totalScore, prevScore)
    
    # Update total maximum score
    users_table.update_item(
        Key = {'email' : email},
        UpdateExpression = f'set problemScores. #a =:s',
        ExpressionAttributeValues={':s' : int(maxScore)},
        ExpressionAttributeNames={'#a':problemName}
    )

    # Checking if this is a firstAC, if so update the #AC of problem table
    if prevScore != 100 and maxScore == 100:
        problems_table.update_item(
            Key = {'problemName' : problemName},
            UpdateExpression = f'set noACs = noACs + :one',
            ExpressionAttributeValues={':one' : 1}
        )
        print("updating score")
                    
                    
    submissions_table.update_item(
        Key={'subId':submissionId},
        UpdateExpression = f'set maxTime = :maxTime, maxMemory=:maxMemory,subtaskScores=:subtaskScores,totalScore=:totalScore',
        ExpressionAttributeValues={':maxTime':maxTime,':maxMemory':maxMemory,':subtaskScores':subtaskScores,':totalScore':totalScore}
    )
    
    print("RETURNING")
    print(maxTime)
    print(maxMemory)
    print(subtaskScores)
    print(totalScore)
    
    return {
        "statusCode":200,
    }