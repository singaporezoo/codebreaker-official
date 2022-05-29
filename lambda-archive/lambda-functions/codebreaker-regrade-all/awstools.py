import boto3
import json
from botocore.exceptions import ClientError
from botocore.client import Config
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb','ap-southeast-1')
problems_table = dynamodb.Table('codebreaker-problems')
submissions_table = dynamodb.Table('codebreaker-submissions')
users_table = dynamodb.Table('codebreaker-users')
lambda_client = boto3.client('lambda')

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
        IndexName = 'problemIndex4',
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
        IndexName = 'problemIndex3',
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