import boto3
import json
import time
from decimal import *
from boto3.dynamodb.conditions import Key

SFclient = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
problems_table = dynamodb.Table('codebreaker-problems')
users_table = dynamodb.Table('codebreaker-users')
submissions_table = dynamodb.Table('codebreaker-submissions')

def getSubmission(subId):
    response = submissions_table.get_item( 
        Key={"subId": subId },
        ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, gradingTime, totalScore, username, #l',
        ExpressionAttributeNames = {'#l': 'language'}
    )
    subDetails = response['Item']

    return subDetails

def getProblemInfo(problemName):
    response= problems_table.query(
        KeyConditionExpression = Key('problemName').eq(problemName)
    )
    problem_info=response['Items'][0]
    return problem_info
    
def getSubmissionsToProblem(problemName):
    response = submissions_table.query(
        IndexName = 'problemIndex',
        KeyConditionExpression = Key('problemName').eq(problemName),
        ProjectionExpression = 'subId',
        ScanIndexForward = False
    )
    return response['Items']

# Sends submission to be regraded by Step Function
def gradeSubmission(problemName,submissionId,username,submissionTime=None,regradeall=False,language='cpp',problemType='Batch',stitch=False):
    regrade=True

    # If no submission time already recorded, this is a new submission
    if submissionTime == None:
        regrade=False
        submissionTime = (datetime.now()+timedelta(hours=8)).strftime("%Y-%m-%d %X")
    
    # Grader required if problem is not batch
    grader = (problemType != 'Batch')

    # Stitching takes place for all submissions made in contest mode that are not sent to analysis mirror
    stitch = stitch

    SF_input = {
        "problemName": problemName,
        "submissionId":int(submissionId),
        "username":username,
        "submissionTime":submissionTime,
        "stitch":stitch,
        "regrade":regrade,
        "regradeall":regradeall,
        "language":language, 
        "grader": grader,
        "problemType": problemType
    }
    
    time.sleep(3)
    stepFunctionARN = "arn:aws:states:ap-southeast-1:354145626860:stateMachine:Codebreaker-grading-v3"
    res = SFclient.start_execution(stateMachineArn = stepFunctionARN, input=json.dumps(SF_input))
    
# UPDATING SCORES AFTER REGRADE OPERATION

def getAllUsersEmails():
    return users_table.scan(ProjectionExpression = 'username, email')['Items']

def getUserInfoFromUsername(username):
    scan_kwargs = {
        'FilterExpression':Key('username').eq(username)
    }
    done = False
    start_key = None
    while not done:
        if start_key:
            scan_kwargs['ExclusiveStartKey']= start_key
        response = users_table.scan(**scan_kwargs)
        res = response.get('Items',[])
        if len(res) > 0:
            return res[0]
        start_key = response.get('LastEvaluatedKey',None)
        done = start_key is None

    placeHolder = {
        'email' : '',
        'school':'',
        'role':'',
        'username':'',
        'problem_scores':{},
        'problem_subtask_scores':{},
    }
    return placeHolder
    
def updateAllScores(problem):
    submissions = submissions_table.query(
        IndexName = 'problemIndex',
        KeyConditionExpression = Key('problemName').eq(problem),
        ProjectionExpression = 'username, totalScore',
        ScanIndexForward = False
    )['Items']

    maxScore = {}
    for i in submissions:
        username = i['username']
        if username not in maxScore:
            maxScore[username] = 0
        maxScore[username] = max(maxScore[username], i['totalScore'])

    useremails = getAllUsersEmails()
    emails = {}
    for i in useremails:
        emails[i['username']] = i['email']

    noACs = 0

    for username, score in maxScore.items():
        users_table.update_item(
            Key = {'email': emails[username]},
            UpdateExpression = f'set problemScores. #a = :s',
            ExpressionAttributeValues = {':s': score},
            ExpressionAttributeNames = {'#a': problem}
        )
        if score == 100:
            noACs += 1

    problems_table.update_item(
        Key = {'problemName': problem},
        UpdateExpression = f'set noACs = :a',
        ExpressionAttributeValues = {':a': noACs}
    )

def updateAllStitchedScores(problem):
    submissions = submissions_table.query(
        IndexName = 'problemIndex',
        KeyConditionExpression = Key('problemName').eq(problem),
        ProjectionExpression = 'username, subtaskScores',
        ScanIndexForward = False
    )['Items']

    subtaskScores = {}
    for i in submissions:
        username = i['username']
        subtasks = i['subtaskScores']
        if username not in subtaskScores:
            subtaskScores[username] = [0] * len(subtasks)
        for j in range(len(subtasks)):
            subtaskScores[username][j] = max(subtaskScores[username][j], subtasks[j])

    subtaskMaxScores = problems_table.query(
        KeyConditionExpression = Key('problemName').eq(problem),
        ProjectionExpression = 'subtaskScores'
    )['Items'][0]['subtaskScores']

    maxScore = {}
    for username, subtasks in subtaskScores.items():
        totalScore = 0
        for i in range(len(subtasks)):
            totalScore += subtasks[i] * int(subtaskMaxScores[i])
        totalScore /= 100
        if int(totalScore) == totalScore:
            totalScore = int(totalScore)
        else:
            totalScore = round(totalScore, 2)
        maxScore[username] = totalScore

    useremails = getAllUsersEmails()
    emails = {}
    for i in useremails:
        emails[i['username']] = i['email']

    noACs = 0

    for username, score in maxScore.items():
        users_table.update_item(
            Key = {'email': emails[username]},
            UpdateExpression = f'set problemScores. #a = :s',
            ExpressionAttributeValues = {':s': score},
            ExpressionAttributeNames = {'#a': problem}
        )
        if score == 100:
            noACs += 1

    problems_table.update_item(
        Key = {'problemName': problem},
        UpdateExpression = f'set noACs = :a',
        ExpressionAttributeValues = {':a': noACs}
    )