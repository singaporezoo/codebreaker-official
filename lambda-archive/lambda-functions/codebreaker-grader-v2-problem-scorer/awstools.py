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

def getUserInfo(email):
    response = users_table.query(
        KeyConditionExpression = Key('email').eq(email)
    )
    user_info = response['Items']
    if len(user_info) == 0:
        newUserInfo = {
            'email' : email,
            'role' : 'disabled',
            'username' : '',
            'problemScores' : {},
            'problemSubtaskScores': {},
        }
        users_table.put_item(Item = newUserInfo)
        return getUserInfo(email)

    return user_info[0]

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
    
def gradeSubmission(lambda_input):
    print(lambda_input)
    res = lambda_client.invoke(
        FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-problem-grader-parallel',
        InvocationType='RequestResponse',
        Payload = json.dumps(lambda_input)
    )

def updateCE(submissionId, compileErrorMessage):
    submissions_table.update_item(
        Key={'subId':submissionId},
        UpdateExpression = f'set compileErrorMessage = :compileErrorMessage',
        ExpressionAttributeValues={':compileErrorMessage':compileErrorMessage}
    )
    
def updateScores(problem, username):
    submissions = submissions_table.query(
        IndexName = 'problemIndex4',
        KeyConditionExpression = Key('problemName').eq(problem),
        ProjectionExpression = 'totalScore',
        FilterExpression = Attr('username').eq(username),
        ScanIndexForward = False
    )['Items']

    if len(submissions) == 0:
        return

    maxScore = 0
    for i in submissions:
        maxScore = max(maxScore, i['totalScore'])

    userInfo = getUserInfoFromUsername(username)
    problemScores = userInfo['problemScores']

    prevScore = 0

    if problem in problemScores:
        prevScore = problemScores[problem]

    users_table.update_item(
        Key = {'email': userInfo['email']},
        UpdateExpression = f'set problemScores. #a = :s',
        ExpressionAttributeValues = {':s': maxScore},
        ExpressionAttributeNames = {'#a': problem}
    )

    if prevScore == 100 and maxScore != 100:
        problems_table.update_item(
            Key = {'problemName': problem},
            UpdateExpression = f'set noACs = noACs - :one',
            ExpressionAttributeValues = {':one':1},
        )
    elif prevScore != 100 and maxScore == 100:
        problems_table.update_item(
            Key = {'problemName': problem},
            UpdateExpression = f'set noACs = noACs + :one',
            ExpressionAttributeValues = {':one': 1}
        )

def updateStitchedScores(problem, username):
    submissions = submissions_table.query(
        IndexName = 'problemIndex3',
        KeyConditionExpression = Key('problemName').eq(problem),
        ProjectionExpression = 'subtaskScores',
        FilterExpression = Attr('username').eq(username),
        ScanIndexForward = False
    )['Items']

    if len(submissions) == 0:
        return

    scores = [0] * len(submissions[0]['subtaskScores'])
    
    for i in submissions:
        for j in range(len(scores)):
            scores[j] = max(scores[j], int(i['subtaskScores'][j]))

    subtaskMaxScores = problems_table.query(
        KeyConditionExpression = Key('problemName').eq(problem),
        ProjectionExpression = 'subtaskScores'
    )['Items'][0]['subtaskScores']
    
    totalScore = 0
    for i in range(len(scores)):
        totalScore += scores[i] * int(subtaskMaxScores[i])
    totalScore /= 100
    
    userInfo = getUserInfoFromUsername(username)
    problemScores = userInfo['problemScores']

    prevScore = 0

    if problem in problemScores:
        prevScore = problemScores[problem]

    maxScore = max(totalScore, prevScore)

    if int(maxScore) == maxScore:
        maxScore = int(maxScore)
    else:
        maxScore = round(maxScore, 2)

    users_table.update_item(
        Key = {'email': userInfo['email']},
        UpdateExpression = f'set problemScores. #a = :s',
        ExpressionAttributeValues = {':s': maxScore},
        ExpressionAttributeNames = {'#a': problem}
    )

    if prevScore != 100 and maxScore == 100:
        problems_table.update_item(
            Key = {'problemName': problem},
            UpdateExpression = f'set noACs = noACs + :one',
            ExpressionAttributeValues = {':one': 1}
        )

def uploadSubmission(submission_upload):
    submissions_table.put_item(Item = submission_upload)
    
def updateScores(problem, username):
    submissions = submissions_table.query(
        IndexName = 'problemIndex4',
        KeyConditionExpression = Key('problemName').eq(problem),
        ProjectionExpression = 'totalScore',
        FilterExpression = Attr('username').eq(username),
        ScanIndexForward = False
    )['Items']

    if len(submissions) == 0:
        return

    maxScore = 0
    for i in submissions:
        maxScore = max(maxScore, i['totalScore'])

    userInfo = getUserInfoFromUsername(username)
    problemScores = userInfo['problemScores']

    prevScore = 0

    if problem in problemScores:
        prevScore = problemScores[problem]

    users_table.update_item(
        Key = {'email': userInfo['email']},
        UpdateExpression = f'set problemScores. #a = :s',
        ExpressionAttributeValues = {':s': maxScore},
        ExpressionAttributeNames = {'#a': problem}
    )

    if prevScore == 100 and maxScore != 100:
        problems_table.update_item(
            Key = {'problemName': problem},
            UpdateExpression = f'set noACs = noACs - :one',
            ExpressionAttributeValues = {':one':1},
        )
    elif prevScore != 100 and maxScore == 100:
        problems_table.update_item(
            Key = {'problemName': problem},
            UpdateExpression = f'set noACs = noACs + :one',
            ExpressionAttributeValues = {':one': 1}
        )

def updateStitchedScores(problem, username):
    submissions = submissions_table.query(
        IndexName = 'problemIndex3',
        KeyConditionExpression = Key('problemName').eq(problem),
        ProjectionExpression = 'subtaskScores',
        FilterExpression = Attr('username').eq(username),
        ScanIndexForward = False
    )['Items']

    if len(submissions) == 0:
        return

    scores = [0] * len(submissions[0]['subtaskScores'])
    
    for i in submissions:
        for j in range(len(scores)):
            scores[j] = max(scores[j], int(i['subtaskScores'][j]))

    subtaskMaxScores = problems_table.query(
        KeyConditionExpression = Key('problemName').eq(problem),
        ProjectionExpression = 'subtaskScores'
    )['Items'][0]['subtaskScores']
    
    totalScore = 0
    for i in range(len(scores)):
        totalScore += scores[i] * int(subtaskMaxScores[i])
    totalScore /= 100
    
    userInfo = getUserInfoFromUsername(username)
    problemScores = userInfo['problemScores']

    prevScore = 0

    if problem in problemScores:
        prevScore = problemScores[problem]

    maxScore = max(totalScore, prevScore)

    if int(maxScore) == maxScore:
        maxScore = int(maxScore)
    else:
        maxScore = round(maxScore, 2)

    users_table.update_item(
        Key = {'email': userInfo['email']},
        UpdateExpression = f'set problemScores. #a = :s',
        ExpressionAttributeValues = {':s': maxScore},
        ExpressionAttributeNames = {'#a': problem}
    )

    if prevScore != 100 and maxScore == 100:
        problems_table.update_item(
            Key = {'problemName': problem},
            UpdateExpression = f'set noACs = noACs + :one',
            ExpressionAttributeValues = {':one': 1}
        )
