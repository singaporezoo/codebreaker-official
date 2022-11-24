import boto3
import json
import subprocess
import time
from time import sleep
import random
import sendemail
from pprint import pprint
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from botocore.client import Config
from boto3.dynamodb.conditions import Key, Attr
from flask import session
import contestmode
import os
import cloudflare

#os.environ['AWS_DEFAULT_REGION']='ap-southeast-1'

s3 = boto3.client('s3','ap-southeast-1')
s3_resource = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
event_client = boto3.client('events')
SFclient = boto3.client('stepfunctions')

CODE_BUCKET_NAME = 'codebreaker-submissions'
STATEMENTS_BUCKET_NAME = 'codebreaker-statements'
SUBMISSION_NUMBER_BUCKET_NAME = 'codebreaker-submission-number'
CHECKERS_BUCKET_NAME = 'codebreaker-checkers'
GRADERS_BUCKET_NAME = 'codebreaker-graders'
ATTACHMENTS_BUCKET_NAME = 'codebreaker-attachments'
TESTDATA_BUCKET_NAME = 'codebreaker-testdata'
SCOREBOARDS_BUCKET_NAME = 'codebreaker-contest-static-scoreboards'

problems_table = dynamodb.Table('codebreaker-problems')
submissions_table = dynamodb.Table('codebreaker-submissions')
users_table = dynamodb.Table('codebreaker-users')
contests_table = dynamodb.Table('codebreaker-contests')
contest_groups_table = dynamodb.Table('codebreaker-contest-groups')
announce_table = dynamodb.Table('codebreaker-announcements')
clarifications_table = dynamodb.Table('codebreaker-clarifications')
end_contest_table = dynamodb.Table('codebreaker-end-contest')
misc_table = dynamodb.Table('codebreaker-misc')

themes = ['light', 'dark', 'pink', 'brown', 'orange', 'custom', 'custom-dark']

#this is a dummy change
subPerPage = 25

# Scanning dynamoDB
def scan(table, ProjectionExpression=None, ExpressionAttributeNames = None, ExpressionAttributeValues = None):
    results = []
    if ProjectionExpression == None:
        # No Expression Attribute Names
        resp = table.scan()
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']
    elif ExpressionAttributeNames != None and ExpressionAttributeValues != None:
        resp = table.scan(
            ProjectionExpression=ProjectionExpression,
            ExpressionAttributeNames = ExpressionAttributeNames,
            ExpressionAttributeValues = ExpressionAttributeValues
        )
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ProjectionExpression=ProjectionExpression,
                ExpressionAttributeNames = ExpressionAttributeNames,
                ExpressionAttributeValues = ExpressionAttributeValues,
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']

    elif ExpressionAttributeNames != None:
        resp = table.scan(
            ProjectionExpression=ProjectionExpression,
            ExpressionAttributeNames = ExpressionAttributeNames,
        )
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ProjectionExpression=ProjectionExpression,
                ExpressionAttributeNames = ExpressionAttributeNames,
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']
    elif ExpressionAttributeValues != None:
        resp = table.scan(
            ProjectionExpression=ProjectionExpression,
            ExpressionAttributeValues = ExpressionAttributeValues
        )
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ProjectionExpression=ProjectionExpression,
                ExpressionAttributeValues = ExpressionAttributeValues,
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']
    else:
        resp = table.scan(
            ProjectionExpression=ProjectionExpression,
        )
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ProjectionExpression=ProjectionExpression,
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']
    return results

def getAllProblems():
    value = scan(problems_table)
    return value
# return problems_table.scan()['Items']

def getAllProblemNames():
    problemNames = problems_table.scan(
        ProjectionExpression = 'problemName'
    )['Items']
    return problemNames

def getAllContestIds():
    contestIds = scan(contests_table, ProjectionExpression='contestId')
    return contestIds

def getAllGroupIds():
    groupIds = scan(contest_groups_table, ProjectionExpression='groupId')
    return groupIds

def getAllProblemsLimited():
    return scan(problems_table, 
        ProjectionExpression = 'problemName, analysisVisible, title, #source2, author, problem_type, noACs, validated, contestLink, superhidden,createdTime,EE,allowAccess,tags',
        ExpressionAttributeNames={'#source2':'source'}
    )

def getAllProblemsHidden():
    return scan(problems_table,
        ProjectionExpression='problemName, analysisVisible, superhidden'
    )

def getAllUsers():
    return scan(users_table)

def getAllUsernames():
    usernames = scan(users_table,
        ProjectionExpression = 'username'
    )
    return usernames

def getProblemInfo(problemName):
    response= problems_table.query(
        KeyConditionExpression = Key('problemName').eq(problemName)
    )
    problem_info=response['Items']
    if len(problem_info) == 0:
        return "This problem doesn't exist"
    if len(problem_info) != 1:
        return "This problem doesn't exist22"

    problem_info = problem_info[0]
    return problem_info

def getTestcase(path):
    tcfile = s3.get_object(Bucket=TESTDATA_BUCKET_NAME, Key=path)
    body = tcfile['Body'].read().decode("utf-8")
    return body

def uploadAttachments(attachments, s3Name):
    s3.upload_fileobj(attachments, ATTACHMENTS_BUCKET_NAME, s3Name, ExtraArgs={"ACL": 'public-read', "ContentType":attachments.content_type})

def getSuperhiddenProblems():
    response = misc_table.query(
        KeyConditionExpression = Key('category').eq('superhiddenProblems')
    )
    return response['Items'][0]['problems']

def setSuperhidden(problemName, superhidden):
    problems_table.update_item(
        Key = {'problemName' : problemName},
        UpdateExpression = f'set superhidden=:l',
        ExpressionAttributeValues={':l':superhidden},
    )
    if superhidden:
        misc_table.update_item(
            Key = {'category': 'superhiddenProblems'},
            UpdateExpression = f'add problems :p',
            ExpressionAttributeValues={':p' : set([problemName])}
        )
    else:
        try:
            misc_table.update_item(
                Key = {'category': 'superhiddenProblems'},
                UpdateExpression = f'delete problems :p',
                ExpressionAttributeValues={':p' : set([problemName])}
            )
        except e:
            pass

def updateProblemInfo(problemName, info): 
    setSuperhidden(problemName, info['superhidden'])
    problems_table.update_item(
        Key = {'problemName' : problemName},
        UpdateExpression = f'set title=:a, #kys=:b, author=:c, problem_type=:d, timeLimit=:e, memoryLimit=:f, fullFeedback=:g, analysisVisible=:h, customChecker=:i,attachments=:j,contestLink=:k,superhidden=:l,createdTime=:m, editorials=:n, editorialVisible=:o, EE=:p',
        ExpressionAttributeValues={':a':info['title'], ':b':info['source'], ':c':info['author'], ':d':info['problem_type'], ':e':info['timeLimit'], ':f':info['memoryLimit'], ':g':info['fullFeedback'], ':h':info['analysisVisible'], ':i':info['customChecker'], ':j':info['attachments'], ':k':info['contestLink'], ':l':info['superhidden'], ':m':info['createdTime'], ':n':info['editorials'], ':o':info['editorialVisible'],':p':info['EE']},
        ExpressionAttributeNames={'#kys':'source'}
    )

def makeAnalysisVisible(problemName):
    problems_table.update_item(
        Key = {'problemName' : problemName},
        UpdateExpression = f'set analysisVisible=:h',
        ExpressionAttributeValues={':h':1},
    )
    setSuperhidden(problemName, False)

def addAllowAccess(problemName):
    problems_table.update_item(
        Key = {'problemName': problemName},
        UpdateExpression = f'set allowAccess=:a',
        ExpressionAttributeValues={':a':[]},
    )

def getProblemStatementHTML(problemName):
    statement = ''
    try:
        htmlfile = s3.get_object(Bucket=STATEMENTS_BUCKET_NAME, Key=f'{problemName}.html') 
        body = htmlfile['Body'].read().decode("utf-8") 
        statement += body
    except s3.exceptions.NoSuchKey as e:
        pass
    try:
        name = f'{problemName}.pdf'
        s3.head_object(Bucket=STATEMENTS_BUCKET_NAME, Key=name)
        if (len(statement) > 0):
            statement += '<br>'
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': STATEMENTS_BUCKET_NAME, 'Key': name},
            ExpiresIn=60)

        statement += '<iframe src=\"' + url + '\" width=\"100%\" height=\"700px\"></iframe>'
    except ClientError as e:
        pass
    if (len(statement) == 0):
        return {'status': 404, 'response':'No statement is currently available'}
    else:
        return {'status': 200, 'response':statement}

def uploadStatement(statement, s3Name):
    s3.upload_fileobj(statement, STATEMENTS_BUCKET_NAME, s3Name)

def uploadChecker(checker, s3Name):
    s3.upload_fileobj(checker, CHECKERS_BUCKET_NAME, s3Name)

def getChecker(problem_id, path):
    checker = s3.get_object(Bucket=CHECKERS_BUCKET_NAME,Key=f"source/{problem_id}.cpp")
    checker = checker['Body'].read().decode('utf-8')
    with open(path,"w") as f:
        f.write(checker)
        f.close()

def getGraderFile(s3path, localpath):
    grader = s3.get_object(Bucket=GRADERS_BUCKET_NAME,Key=s3path)
    grader = grader['Body'].read().decode('utf-8')
    with open(localpath,"w") as f:
        f.write(grader)
        f.close()

def deleteStatement(statementName):
    s3.delete_object(Bucket=STATEMENTS_BUCKET_NAME, Key=statementName)

def updateSubtaskInfo(problemName, info):
    problems_table.update_item(
        Key = {'problemName' : problemName},
        UpdateExpression = f'set subtaskScores=:a, subtaskDependency=:b',
        ExpressionAttributeValues={':a':info['subtaskScores'], ':b':info['subtaskDependency']}
    )

def updateEditorialInfo(problemName, info):
    problems_table.update_item(
        Key = {'problemName': problemName},
        UpdateExpression = f'set editorials=:a',
        ExpressionAttributeValues = {':a':info['editorials']}
    )

def updateAccessInfo(problemName, info):
    problems_table.update_item(
        Key = {'problemName': problemName},
        UpdateExpression = f'set allowAccess=:a',
        ExpressionAttributeValues = {':a':info['allowAccess']}
    )

def testcaseUploadLambda(problemName):
    lambda_input = {"problemName": problemName}
    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-problem-upload-2', InvocationType='Event', Payload = json.dumps(lambda_input))

def updateCountLambda(problemName):
    lambda_input = {"problemName": problemName}
    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-update-testcaseCount', InvocationType='RequestResponse', Payload = json.dumps(lambda_input))

def uploadCode(sourceName, uploadTarget):
    s3.upload_file(sourceName, CODE_BUCKET_NAME, uploadTarget)

def gradeSubmission(problemName,submissionId,username,submissionTime=None,regradeall=False,language='cpp'):
    regrade=False
    if submissionTime is None:
        regrade=True
        submissionTime = (datetime.now()+timedelta(hours=8)).strftime("%Y-%m-%d %X")
    stitch = contestmode.contest() and contestmode.stitch() and contestmode.contestId() != 'analysismirror'
    lambda_input = {"problemName": problemName, "submissionId":submissionId,"username":username,"submissionTime":submissionTime,"stitch":stitch,"regrade":regrade,"regradeall":regradeall,"language":language}
    stepFunctionARN = "arn:aws:states:ap-southeast-1:354145626860:stateMachine:CodebreakerGradingv2"
    res = SFclient.start_execution(stateMachineArn = stepFunctionARN, input = json.dumps(lambda_input))


def updateScores(problemName):
    stitch = contestmode.contest() and contestmode.stitch()
    lambda_input = {"problemName": problemName,"stitch":stitch}
    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-regrade-all', InvocationType='Event', Payload = json.dumps(lambda_input))

def getSubmission(subId, full=True):
    try:
        if full:
            response= submissions_table.get_item( Key={ "subId": subId } )
        else:
            response = submissions_table.get_item( 
                Key={"subId": subId },
                ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, gradingTime, totalScore, username, #l',
                ExpressionAttributeNames = {'#l': 'language'}
            )
        subDetails = response['Item']

        if subDetails['language'] == 'py':
            pyfile = s3.get_object(Bucket=CODE_BUCKET_NAME, Key=f'source/{subId}.py')
            code = pyfile['Body'].read().decode("utf-8")
            subDetails['code'] = code
        else:
            try:
                cppfile = s3.get_object(Bucket=CODE_BUCKET_NAME, Key=f'source/{subId}.cpp')
                code = cppfile['Body'].read().decode("utf-8")
                subDetails['code'] = code
            except:
                cppfile = s3.get_object(Bucket=CODE_BUCKET_NAME, Key=f'source/{subId}A.cpp')
                codeA = cppfile['Body'].read().decode("utf-8")
                subDetails['codeA'] = codeA
                cppfile = s3.get_object(Bucket=CODE_BUCKET_NAME, Key=f'source/{subId}B.cpp')
                codeB = cppfile['Body'].read().decode("utf-8")
                subDetails['codeB'] = codeB

        return subDetails
    except KeyError:
        return None

def batchGetSubmissions(start, end):
    submissions = []
    for i in range(start, end+1):
        submissions.append({'subId' : i})
    response = dynamodb.batch_get_item(
        RequestItems={
            'codebreaker-submissions': {
                'Keys': submissions,            
                'ConsistentRead': True            
                }
            },
        ReturnConsumedCapacity='TOTAL'
    )
    return response

def batchGetSubmissionsLimited(start, end):
    submissions = []
    for i in range(start, end+1):
        submissions.append({'subId' : i})
    response = dynamodb.batch_get_item(
        RequestItems={
            'codebreaker-submissions': {
                'Keys': submissions,            
                'ConsistentRead': True,
                'ProjectionExpression': 'problemName, submissionTime, username'
                }
            },
        ReturnConsumedCapacity='TOTAL'
    )
    return response

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
            'theme' : 'light',
            'problemScores' : {},
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
        'nation': '',
        'username':'',
        'problemScores':{},
    }
    return placeHolder

def getCurrentUserInfo():
    try:
        email =  dict(session)['profile']['email']
        user_info =  getUserInfo(email)
        return user_info
    except KeyError as e:
        return None
    return None

def updateUserInfo(email, username, fullname, school, theme, hue, nation):
    users_table.update_item(
        Key = {'email' : email},
        UpdateExpression = f'set username =:u, fullname=:f, school =:s, theme =:t, hue=:h, nation=:n',
        ExpressionAttributeValues={':u' : username, ':f' : fullname, ':s' : school, ':t' : theme, ':h':hue, ':n': nation}
    )

def editUserRole(info,newrole,changedby):
    if info['role'] == newrole:
        return

    email = info['email']
    users_table.update_item(
        Key = {'email' : email},
        UpdateExpression = f'set #ts =:r',
        ExpressionAttributeValues={':r' : newrole},
        ExpressionAttributeNames={'#ts':'role'}
    )

    emailType = sendemail.ROLE_CHANGED

    if newrole == 'disabled' or newrole == 'locked':
        emailType = sendemail.ACCOUNT_DISABLED

    if (newrole != 'disabled' and newrole != 'locked') and (info['role'] == 'disabled' or info['role'] == 'locked'):
        emailType = sendemail.ACCOUNT_ENABLED

    sendemail.sendEmail(info,emailType,changedby,newrole)

def getNextSubmissionId():
    res = lambda_client.invoke(
        FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-submission-queue-response',
        InvocationType = 'RequestResponse'
    )
    submission_index = json.load(res["Payload"])
    return submission_index['submissionId']


def getSubmissionsList(pageNo, problem, username): #this is for all submissions only
    if username == None and problem == None:
        latest = int(getNumberOfSubmissions())
        end = latest - (pageNo-1)* subPerPage
        start = max(1, end-subPerPage+1)

        if end < 0:
            return []

        response = batchGetSubmissions(start,end)
        submissions = response['Responses']['codebreaker-submissions']
        return submissions
    elif username != None and problem == None:
        response = submissions_table.query(
            IndexName = 'usernameIndex3',
            KeyConditionExpression=Key('username').eq(username),
            Limit = (pageNo+1)*subPerPage + 2,
            ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, totalScore, username, #a',
            ExpressionAttributeNames = {'#a': 'language'},
            ScanIndexForward = False
        )
        return response['Items']
    elif username == None and problem != None:
        response = submissions_table.query(
            IndexName = 'problemIndex5',
            KeyConditionExpression=Key('problemName').eq(problem),
            ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, totalScore, username, #a',
            ExpressionAttributeNames = {'#a': 'language'},
            Limit = (pageNo+1)*subPerPage + 2,
            ScanIndexForward = False
        )
        return response['Items']
    else:
        response = submissions_table.query(
            IndexName = 'problemIndex5',
            KeyConditionExpression=Key('problemName').eq(problem),
            ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, totalScore, username, #a',
            ExpressionAttributeNames = {'#a': 'language'},
            FilterExpression = Attr('username').eq(username),
            ScanIndexForward = False
        )
        return response['Items']

def getSubmissionsToProblem(problemName):
    response = submissions_table.query(
        IndexName = 'problemIndex5',
        KeyConditionExpression = Key('problemName').eq(problemName),
        ProjectionExpression = 'subId',
        ScanIndexForward = False
    )
    return response['Items']

def getNumberOfSubmissions():
    subId = s3.get_object(Bucket=SUBMISSION_NUMBER_BUCKET_NAME,Key=f'submissionNumber.txt')['Body'].read().decode('utf-8')
    subId = int(subId)
    return subId-1

def createProblemWithId(problem_id):
    info = {}
    info['title'] = problem_id
    info['source'] = 'Unknown Source'
    info['author'] = ''
    info['problem_type'] = 'Batch'
    info['timeLimit'] = 1
    info['memoryLimit'] = 1024
    info['fullFeedback'] = True
    info['analysisVisible'] = False
    info['customChecker'] = False
    info['attachments'] = False
    info['contestLink'] = ""
    info['superhidden'] =  False
    info['contestUsers'] = []
    info['createdTime'] = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %X")
    info['editorials'] = []
    info['editorialVisible'] = False
    info['EE'] = False
    info['']
    updateProblemInfo(problem_id, info)
    subtasks = {}
    subtasks['subtaskScores'] = []
    subtasks['subtaskDependency'] = []
    subtasks['subtaskScores'].append(100)
    subtasks['subtaskDependency'].append('1')
    updateSubtaskInfo(problem_id, subtasks)
    extras = {}
    extras['noACs'] = 0
    extras['testcaseCount'] = 0
    problems_table.update_item(
        Key = {'problemName' : problem_id},
        UpdateExpression = f'set noACs=:a, testcaseCount=:b',
        ExpressionAttributeValues={':a':extras['noACs'], ':b':extras['testcaseCount']}
    )
    validateProblem(problem_id)

def getAllContests():
    return scan(contests_table,
        ProjectionExpression = 'contestId, contestName, startTime, endTime, #PUBLIC, #DURATION, #USERS',
        ExpressionAttributeNames={ "#PUBLIC": "public", "#DURATION" : "duration", '#USERS':'users' } #not direct cause users is a reserved word
    )

def getAllContestsLimited():
    return scan(contests_table,
        ProjectionExpression = 'contestId, contestName, startTime, endTime, #PUBLIC',
        ExpressionAttributeNames={ "#PUBLIC": "public"} #not direct cause users is a reserved word
    )

def getContestInfo(contestId):
    response= contests_table.query(
        KeyConditionExpression = Key('contestId').eq(contestId)
    )
    contest_info=response['Items']
    if len(contest_info) == 0:
        return None
    return contest_info[0]

def addParticipation(contestId, username):

    if username != "ALLUSERS":
        #change this later
        contests_table.update_item(
            Key = {'contestId' : contestId},
            UpdateExpression = f'set #USERS.#username = :t',
            ExpressionAttributeNames={ "#username": username, "#USERS" : "users" }, #not direct cause users is a reserved word
            ExpressionAttributeValues={ ":t" : datetime.now().strftime("%Y-%m-%d %X") }
        )

    response = contests_table.query(
        KeyConditionExpression = Key('contestId').eq(contestId)
    )
    contest_info=response['Items'][0]
    endTimeStr = contest_info['endTime']
    duration = contest_info['duration']

    if endTimeStr == "Unlimited" and duration == 0:
        return

    if endTimeStr != "Unlimited" and username == "ALLUSERS":
        endTime = datetime.strptime(endTimeStr, "%Y-%m-%d %X") - timedelta(hours = 8)
        scheduleEndParticipation(contestId, username, endTime)
        #cmd = f"echo \"python3 -c 'import awstools; awstools.endParticipation(\\\"{contestId}\\\", \\\"{username}\\\") ' \" | at {endTimeStrAt}"
        return

    stopIndividual = False
    if endTimeStr == "Unlimited":
        stopIndividual = True
        endTime = datetime.now() + timedelta(minutes = int(duration))
    else:
        endTime = datetime.strptime(endTimeStr, "%Y-%m-%d %X") - timedelta(hours = 8)#based on official end Time
        duration = contest_info['duration']
        if duration != 0:
            #print(endTime)
            #print(datetime.now() + timedelta(minutes = int(duration)))
            if endTime > datetime.now() + timedelta(minutes = int(duration)):
                endTime = datetime.now() + timedelta(minutes = int(duration+1))
                stopIndividual = True
            else:
                stopIndividual = False

    endTimeStrAt = endTime.strftime("%H:%M %Y-%m-%d") #for parsing in the at function

    if stopIndividual:
        scheduleEndParticipation(contestId, username, endTime)
        #cmd = f"echo \"python3 -c 'import awstools; awstools.endParticipation(\\\"{contestId}\\\", \\\"{username}\\\") ' \" | at {endTimeStrAt}"
    else:
        pass
    #print(f"{username} stopping at contest end time")

def scheduleEndParticipation(contestId, username, time):
    if time < datetime.now():
        return
    import app
    app.addEndParticipation(contestId, username, time)

def endParticipation(contestId, username):
    #print(f"ending {contestId}, {username}")
    lambda_input = {"contestId":contestId, "username":username}
    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:stopcontestwindow', InvocationType='Event', Payload = json.dumps(lambda_input))

def validateProblem(problemId):
    lambda_input = {'problemName':problemId}
    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-problem-verification', InvocationType='RequestResponse', Payload = json.dumps(lambda_input))

def uploadCompiledChecker(sourceName, uploadTarget):
    s3.upload_file(sourceName, CHECKERS_BUCKET_NAME, uploadTarget)

def uploadGrader(sourceName, uploadTarget):
    s3.upload_fileobj(sourceName, GRADERS_BUCKET_NAME, uploadTarget)

def updateContestInfo(contest_id, info):
    if info['endTime'] != "Unlimited":
        testtime = datetime.strptime(info['endTime'], "%Y-%m-%d %X")
    testtime = datetime.strptime(info['startTime'], "%Y-%m-%d %X")
    contests_table.update_item(
        Key = {'contestId' : contest_id},
        UpdateExpression = f'set contestName=:b, #wtf=:c, problems=:d, #kms=:e, #die=:f, scores=:g, startTime=:h, endTime=:i, description=:j, publicScoreboard=:k, editorial=:l, editorialVisible=:m, subLimit=:n, subDelay=:o',
        ExpressionAttributeValues={':b':info['contestName'], ':c':info['duration'], ':d':info['problems'], ':e':info['public'], ':f':info['users'], ':g':info['scores'], ':h':info['startTime'], ':i':info['endTime'], ':j':info['description'], ':k':info['publicScoreboard'], ':l':info['editorial'], ':m':info['editorialVisible'], ':n':info['subLimit'], ':o':info['subDelay']},
        ExpressionAttributeNames={'#wtf':'duration', '#kms':'public', '#die':'users'}
    )
    addParticipation(contest_id, "ALLUSERS")
    recalcContestInfo()
    return True

def createContestWithId(contest_id):
    info = {}
    info['description'] = ''
    info['contestId'] = contest_id
    info['contestName'] = 'New Contest'
    info['duration'] = 0
    info['problems'] = []
    info['public'] = False
    info['publicScoreboard'] = False
    info['users'] = {}
    info['scores'] = {}
    info['startTime'] = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %X")
    info['endTime'] =  "Unlimited"
    info['editorial'] = ""
    info['editorialVisible'] = False
    info['subLimit'] = -1
    info['subDelay'] = 10
    updateContestInfo(contest_id, info)

def createGroupWithId(group_id):
    info = {}
    info['description'] = ''
    info['groupId'] = group_id
    info['groupName'] = 'New Group'
    info['contests'] = []
    info['contestGroups'] = []
    info['visible'] = False
    updateContestGroupInfo(group_id, info)

def count_objects(table_name):
    cmd = f'aws dynamodb scan --table-name {table_name} --select "COUNT"'
    # obj = dynamodb.scan(TableName=table_name,Select='COUNT')
    process = subprocess.run(cmd, shell=True, capture_output=True)
    output = process.stdout
    obj=output.decode()
    return json.loads(obj)['Count']

def getRankings():
    H = []

    def sm(y):
        r = [0,0,0]
        res=0
        for i in y:
            if y[i]==100:r[0]+=1
            elif y[i]==0:r[2]+=1
            else: r[1]+=1
            res+=float(y[i])
            res=float(res)
            if int(res)  == res:
                res=int(res)
        res = round(res, 2)
        return [res,r[0],r[1],r[2]]

    def res(x):
        for ele in x:
            if ele['username'] == '':
                continue
            t = sm(ele['problemScores'])
            if t[0] != 0:
                H.append([t[0],t[1],t[2],t[3],ele['username'],ele['nation']])

    users = scan(users_table, ProjectionExpression='username,problemScores,nation')
    res(users)

    H.sort()
    H.reverse()

    # Inserting tied-indices
    index = 0
    for i in range(len(H)):
        if (H[i][0] != H[index][0]):
            index = i
        H[i].append(index+1)
    return H

def get_countries():
    subs = scan(users_table,ProjectionExpression='username,nation')
    nations = []
    nations += [i['nation'] for i in subs if i['username'] != '']

    nations = list(set(nations))
    BANNED_NATIONS = ['Outer Space', 'N/A']
    nations = [i for i in nations if i not in BANNED_NATIONS]
    return nations

def findLength(table, primaryKey):
    ans = 0
    subs = scan(table, ProjectionExpression=f'{primaryKey}')
    if primaryKey == 'username':
        subs = [i for i in subs if i['username'] != '']
    ans += len(subs)
    return ans

def getSubmissionId():
    subId = s3.get_object(Bucket='codebreaker-submission-number',Key=f'submissionNumber.txt')['Body'].read().decode('utf-8')
    subId = int(subId)
    subId = 1000*round(subId/1000)
    return subId

def mostSubmittedProblems():
    curSub = getSubmissionId()
    subCounts = {}
    while(curSub > 0):
        subs = batchGetSubmissionsLimited(curSub - 99, curSub)['Responses']['codebreaker-submissions']
        stop = False
        for sub in subs:
            if type(sub) == str:
                continue
            subTime = datetime.strptime(sub['submissionTime'], "%Y-%m-%d %X")
            if subTime + timedelta(days = 7) < datetime.now():
                stop = True
            else:
                problem = sub['problemName']
                if problem not in subCounts:
                    subCounts[problem] = 0
                subCounts[problem] += 1
        if stop:
            break
        curSub = curSub - 100
    top = sorted(subCounts, key=subCounts.get, reverse=True)[:5]
    res = {}
    for i in top:
        res[i] = subCounts[i]
    return res

def mostAttemptedProblems():
    curSub = getSubmissionId()
    uniqueSubs = {}
    while(curSub > 0):
        subs = batchGetSubmissionsLimited(curSub - 99, curSub)['Responses']['codebreaker-submissions']
        stop = False
        for sub in subs:
            if type(sub) == str:
                continue
            subTime = datetime.strptime(sub['submissionTime'], "%Y-%m-%d %X")
            if subTime + timedelta(days = 7) < datetime.now():
                stop = True
            else:
                uniqueSubs[f"{sub['problemName']};{sub['username']}"] = 0
        if stop:
            break
        curSub = curSub - 100
    subCounts = {}
    for s in uniqueSubs.keys():
        problem = s.split(';')[0]
        if problem not in subCounts:
            subCounts[problem] = 0
        subCounts[problem] += 1
    top = sorted(subCounts, key=subCounts.get, reverse=True)[:5]
    res = {}
    for i in top:
        res[i] = subCounts[i]
    return res

def recalcContestInfo():
    try:
        data = json.load(open('homepage.json'))
        contests = getAllContestsLimited()
        contests = [i for i in contests if i['public']]
        contests = [i for i in contests if i['endTime'] != "Unlimited"]
        data['contests'] = contests
        json.dump(data, open('homepage.json', 'w'))
    except Exception as e:
        homepageInfo(recalc=True)

def homepageInfo(recalc = False):
    try:
        data = json.load(open('homepage.json'))
        parseDate = datetime.strptime(data['date'], "%d/%m/%Y")
        problems = int(data['problems'])
        users = int(data['users'])
        subs = int(data['subs'])
        nations = int(data['nations'])
        mostsub = data['mostsub']
        mostattempt = data['mostattempt']
        contests = data['contests']
        pageviews = data['pageviews']
        subsperday = data['subsperday']
    except Exception as e:
        recalc = True

    if recalc or parseDate + timedelta(days=1) < datetime.now():
        print("recalculate homepage data")
        print(datetime.now())
        problems = findLength(problems_table,'problemName')
        users = findLength(users_table,'username')
        subs = getSubmissionId()
        nations = len(get_countries())
        mostattempt = mostAttemptedProblems()
        mostsub = mostSubmittedProblems()
        contests = getAllContestsLimited()
        contests = [i for i in contests if i['public']]
        contests = [i for i in contests if i['endTime'] != "Unlimited"]
        pageviews = cloudflare.main()
        subsperday = getSubsPerDay()
        parseDate = datetime.now().strftime("%d/%m/%Y")
        json.dump({'date':parseDate,'users':users,'problems':problems,'subs':subs,'nations':nations,'mostsub':mostsub,'mostattempt':mostattempt,'contests':contests,'pageviews':pageviews,'subsperday':subsperday}, open('homepage.json', 'w'))

    return {'users':users,'problems':problems,'subs':subs,'nations':nations,'mostsub':mostsub,'mostattempt':mostattempt,'contests':contests,'pageviews':pageviews,'subsperday':subsperday}

def filterSpace(x):
    y = [i for i in list(x) if i != ' ']
    return ''.join(y)

def updateContestProblems(contestId, problems):
    contestId = filterSpace(contestId)
    problems = json.loads(filterSpace(problems))
    contests_table.update_item(
        Key = {'contestId' : str(contestId)},
        UpdateExpression = f'set problems=:a',
        ExpressionAttributeValues = {':a':problems}
    )

def updateContestGroupContests(contestGroupId, contests):
    contestGroupId = filterSpace(contestGroupId)
    contests = json.loads(filterSpace(contests))
    contest_groups_table.update_item(
        Key = {'groupId': str(contestGroupId)},
        UpdateExpression = f'set contests=:a',
        ExpressionAttributeValues = {':a':contests}
    )

def updateContestGroupGroups(contestGroupId, groups):
    contestGroupId = filterSpace(contestGroupId)
    groups = json.loads(filterSpace(groups))
    contest_groups_table.update_item(
        Key = {'groupId': str(contestGroupId)},
        UpdateExpression = f'set contestGroups=:a',
        ExpressionAttributeValues = {':a':groups}
    )

def getContestGroupInfo(groupId):
    info = contest_groups_table.get_item(Key={ "groupId": groupId })
    if 'Item' in info:
        return info['Item']
    else:
        return 'Not Found'

def updateContestGroupInfo(groupId, info):
    contest_groups_table.update_item(
        Key = {'groupId' : groupId},
        UpdateExpression = f'set contests=:a, description=:b, groupName=:c, visible=:d, contestGroups=:e',
        ExpressionAttributeValues = {':a':info['contests'], ':b':info['description'], ':c':info['groupName'], ':d':info['visible'], ':e':info['contestGroups']}
    )


def getContestScore(contestId, username):
    contestinfo = getContestInfo(contestId)

    start = datetime.strptime(contestinfo['startTime'], "%Y-%m-%d %X")
    now = datetime.now() + timedelta(hours = 8)

    past = False
    duration = contestinfo['duration']
    contestName = contestinfo['contestName']
    endTime = contestinfo['endTime']
    public = contestinfo['public']

    if endTime != "Unlimited":
        end = datetime.strptime(endTime, "%Y-%m-%d %X")
        past = (end < now)

    totalscore = len(contestinfo['problems'])*100
    if username in contestinfo['scores']:
        score = 0
        x = contestinfo['scores'][username]
        for i in x:
            score += x[i]
        return {'userscore':score, 'totalscore':totalscore,'duration':duration,'contestName':contestName, 'public':public}
    return {'userscore':None, 'totalscore':totalscore,'duration':duration,'contestName':contestName, 'public':public}

def getAllContestGroups():
    return scan(contest_groups_table,
        ProjectionExpression = 'groupId, groupName, visible',
    )


def getAllContestGroupIds():
    return scan(contest_groups_table,
        ProjectionExpression = 'groupId',
    )

def getAllAnnounces():
    return scan(announce_table, 
        ProjectionExpression='announceId, priority, visible, aSummary, aTitle, adminOnly, contestLink'
    )

def updateAnnounce(announceId, info):
    announce_table.update_item(
        Key = {'announceId': announceId},
        UpdateExpression = f'set priority=:a, visible=:b, aTitle=:c, aSummary=:d, aText=:e, adminOnly=:f, contestLink = :g',
        ExpressionAttributeValues={':a':info['priority'], ':b':info['visible'], ':c':info['aTitle'], ':d':info['aSummary'], ':e':info['aText'], ':f':info['adminOnly'], ':g':info['contestLink']}
    )

def createAnnounceWithId(announceId):
    ann = getAllAnnounces()
    info = {}
    info['priority'] = 1
    for an in ann:
        info['priority'] = max(info['priority'], an['priority']+1)
    info['announceId'] = announceId
    info['visible'] = False
    info['adminOnly'] = False
    info['aTitle'] = announceId
    info['aSummary'] = "default summary of announce"
    info['aText'] = "default text of announce"
    info['contestLink'] = ""
    updateAnnounce(announceId, info)

def getAnnounceWithId(announceId):
    response=announce_table.query(
        KeyConditionExpression = Key('announceId').eq(announceId)
    )
    info=response['Items']
    if len(info) == 0:
        return "This announcement doesn't exist"
    if len(info) != 1:
        return "An error has occurred"
    info = info[0]
    return info

def checkScoreboard(contestId):
    success = True
    try:
        s3_resource.Object(SCOREBOARDS_BUCKET_NAME, f'{contestId}.csv').load()
    except:
        success = False
    return success

def getScoreboard(path):
    tcfile = s3.get_object(Bucket=SCOREBOARDS_BUCKET_NAME, Key=path)
    body = tcfile['Body'].read().decode("utf-8")
    return body

def generateNewScoreboard(contestId):
    lambda_input = {"contestId": contestId}
    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:codebreaker-generate-contest-scoreboard', InvocationType='RequestResponse', Payload = json.dumps(lambda_input))
    if getScoreboard(f'{contestId}.csv'):
        return 'Success'
    return 'Failure'

def isAllowedAccess(problem_info, userInfo):
    if problem_info['analysisVisible']:
        return True

    if userInfo == None:
        return False

    if userInfo['role'] == 'superadmin':
        return True

    if userInfo['role'] in ['member', 'admin']:
        if 'contestUsers' in problem_info and userInfo['username'] in problem_info['contestUsers']:
            return True

    # Only admin users beyond this point
    if userInfo['role'] == 'admin':
        if 'allowAccess' in problem_info and userInfo['username'] in problem_info['allowAccess']:
            # Admin that is explicitly allowed access
            return True

        if 'superhidden' in problem_info and problem_info['superhidden']:
            # Super hidden blocks all remaining admins except those with special access
            return False

        return True

    return False

def isAllowedAdminAccess (problem_info, userInfo):
    if userInfo == None:
        return False

    if userInfo['role'] == 'superadmin':
        return True

    if userInfo['role'] == 'admin':
        if 'allowAccess' in problem_info and userInfo['username'] in problem_info['allowAccess']:
            # Admin that is explicitly allowed access
            return True

        if 'superhidden' in problem_info and problem_info['superhidden']:
            # Super hidden blocks all remaining admins except those with special access
            return False

        return True
    return False

def grantContestUserAccess (problemName, username):
    problems_table.update_item(
        Key={'problemName': problemName},
        UpdateExpression = f'set contestUsers = list_append(contestUsers, :a)',
        ExpressionAttributeValues = {':a': username}
    )

def updateCommunicationFileNames(problemName, info):
    problems_table.update_item(
        Key = {'problemName' : problemName},
        UpdateExpression = f'set nameA=:a, nameB=:b',
        ExpressionAttributeValues = {':a':info['nameA'], ':b':info['nameB']}
    )

def getNextClarificationId():
    res = lambda_client.invoke(
        FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-next-clarification-id',
        InvocationType = 'RequestResponse'
    )
    return json.load(res['Payload'])['clarificationId']

def updateClarificationInfo(clarificationId, info):
    clarifications_table.update_item(
        Key = {'clarificationId':clarificationId},
        UpdateExpression = f'set askedBy=:a,question=:b,problemId=:c,answer=:d,answeredBy=:e',
        ExpressionAttributeValues={':a':info['askedBy'],':b':info['question'],':c':info['problemId'],':d':info['answer'],':e':info['answeredBy']}
    )

def createClarification(username, question, problemId):
    clarificationId = getNextClarificationId()
    info = {}
    info['askedBy'] = username
    info['question'] = question
    info['problemId'] = problemId
    info['answer'] = ""
    info['answeredBy'] = ""
    updateClarificationInfo(clarificationId, info)

def getClarificationInfo(clarificationId):
    response = clarifications_table.query(
        KeyConditionExpression = Key('clarificationId').eq(clarificationId)
    )
    clarification_info = response['Items']
    if len(clarification_info) == 0:
        return None
    return clarification_info[0]

def getClarificationsByUser(username):
    response = clarifications_table.query(
        IndexName = 'askedByIndex',
        KeyConditionExpression = Key('askedBy').eq(username),
    )
    return response['Items']

def getAllClarifications():
    return scan(clarifications_table)

def getRecommendedProblems(user):
    lambda_input = {'user':user}
    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-recommend-problem', InvocationType='RequestResponse', Payload = json.dumps(lambda_input))
    return json.load(res["Payload"])

def getAllEndContests():
    endcontests = scan(end_contest_table)
    for e in endcontests:
        e['endtime'] = datetime.strptime(e['endtime'],"%Y-%m-%d %X")
    return endcontests

def updateEndContest(eventId, time):
    end_contest_table.update_item(
        Key = {'eventId': eventId},
        UpdateExpression = f'set endtime=:t',
        ExpressionAttributeValues = {':t':time.strftime("%Y-%m-%d %X")}
    )

def removeEndContest(eventId):
    end_contest_table.delete_item(
        Key = {'eventId':eventId}
    )

def updateTags(problemName, tags):
    # Tags is an array
    problems_table.update_item(
        Key = {'problemName': problemName},
        UpdateExpression = f'set tags =:a',
        ExpressionAttributeValues = {':a':tags}
    )

def findLastSubOfDay(date):
    low = 0 
    high = 200000
    while high > low:
        mid = int((low+high + 1)/2)
        submission = getSubmission(mid, False)
        if submission != None and date >= submission["submissionTime"].split(' ')[0]:
            low = mid
        else:
            high = mid - 1
    return low

def getSubsPerDay():
    lastSubOfDay = misc_table.query(
        KeyConditionExpression = Key('category').eq('lastSubOfDay')
    )['Items'][0]['lastSubOfDay']

    changed = False

    weekBeforeDate = datetime.now() - timedelta(days=9)
    weekBefore = weekBeforeDate.strftime('%Y-%m-%d')

    # if date is more than a week away, delete it
    keys = list(lastSubOfDay.keys())
    for key in keys:
        if key <= weekBefore:
            lastSubOfDay.pop(key)
            changed = True

    # if important date isn't here, calculate it
    for i in range(1,9):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')

        if date not in lastSubOfDay:
            lastSubOfDay[date] = findLastSubOfDay(date)
            changed = True

    # if changed, update DB
    if changed:
        print("changed")
        misc_table.update_item(
            Key = {'category': 'lastSubOfDay'},
            UpdateExpression = f'set lastSubOfDay=:s',
            ExpressionAttributeValues={':s': lastSubOfDay}
        )

    subsPerDay = {}

    for i in range(1,8):
        curDay = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        prevDay = (datetime.now() - timedelta(days=i+1)).strftime('%Y-%m-%d')

        subsPerDay[curDay] = lastSubOfDay[curDay] - lastSubOfDay[prevDay]
    
    subsPerDay = [int(value) for key, value in subsPerDay.items()][::-1]

    return subsPerDay

if __name__ == '__main__':
    # PLEASE KEEP THIS AT THE BOTTOM
    # THIS IS FOR DEBUGGING AND WILL ONLY BE ACTIVATED IF YOU DIRECTLY RUN THIS FILE
    # IT DOES NOT OUTPUT ANYTHING ONTO TMUX
    # print("TESTING")
    # print(getProblemStatementHTML('potatocb'))
    # print(getProblemStatementHTML('helloworld'))
    problems = [i['problemName'] for i in getAllProblemNames()]
    for problem in problems:
        problems_table.update_item(
            Key = {'problemName': problem},
            UpdateExpression = f'set contestUsers=:s',
            ExpressionAttributeValues={':s': []}
        )
        print(problem)
    print(problems)
