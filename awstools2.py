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

judgeName = 'codebreaker'
s3 = boto3.client('s3','ap-southeast-1')
s3_resource = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')
event_client = boto3.client('events')
iam_client = boto3.client('iam')
sts_client = boto3.client('sts')
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
counters_table = dynamodb.Table(f'codebreaker-global-counters')

themes = ['light', 'dark', 'pink', 'brown', 'orange', 'alien', 'custom', 'custom-dark']

subPerPage = 25

def updateContestInfo(contest_id, info):
    if info['endTime'] != "Unlimited":
        testtime = datetime.strptime(info['endTime'], "%Y-%m-%d %X")
    testtime = datetime.strptime(info['startTime'], "%Y-%m-%d %X")
    contests_table.update_item(
        Key = {'contestId' : contest_id},
        UpdateExpression = f'set contestName=:b, #c=:c, problems=:d, #e=:e, #f=:f, scores=:g, startTime=:h, endTime=:i, description=:j, publicScoreboard=:k, editorial=:l, editorialVisible=:m, subLimit=:n, subDelay=:o',
        ExpressionAttributeValues={':b':info['contestName'], ':c':info['duration'], ':d':info['problems'], ':e':info['public'], ':f':info['users'], ':g':info['scores'], ':h':info['startTime'], ':i':info['endTime'], ':j':info['description'], ':k':info['publicScoreboard'], ':l':info['editorial'], ':m':info['editorialVisible'], ':n':info['subLimit'], ':o':info['subDelay']},
        ExpressionAttributeNames={'#c':'duration', '#e':'public', '#f':'users'}
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
    resp = counters_table.query(
        KeyConditionExpression = Key('counterId').eq('submissionId')
    )
    print(resp)
    subId = int(resp['Items'][0]['value'])
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
        ExpressionAttributeValues = {':a': [username]}
    )

def updateCommunicationFileNames(problemName, info):
    problems_table.update_item(
        Key = {'problemName' : problemName},
        UpdateExpression = f'set nameA=:a, nameB=:b',
        ExpressionAttributeValues = {':a':info['nameA'], ':b':info['nameB']}
    )

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

# CALCULATES NUMBER OF SUBMISSIONS PER DAY FOR 1 WEEK (FOR HOMEPAGE)
def getSubsPerDay():

    # HELPER FUNCTION THAT BINARY SEARCHES FOR LAST SUBMISSION OF DAY
    def findLastSubOfDay(date):
        low = 0 
        high = 3000000
        while high > low:
            mid = int((low+high + 1)/2)
            submission = getSubmission(mid, False)
            if submission != None and date >= submission["submissionTime"].split(' ')[0]:
                low = mid
            else:
                high = mid - 1
        return low


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

# UPLOAD CODE OF SUBMISSION TO S3 
# Used in problem page for submissions and submissions page for regrading
def uploadSubmission(code, s3path):
    s3_resource.Object(CODE_BUCKET_NAME, s3path).put(Body=code)

# Sends submission to be regraded by Step Function
def gradeSubmission(problemName,submissionId,username,submissionTime=None,regradeall=False,language='cpp',problemType='Batch'):
    regrade=True

    # If no submission time already recorded, this is a new submission
    if submissionTime == None:
        regrade=False
        submissionTime = (datetime.now()+timedelta(hours=8)).strftime("%Y-%m-%d %X")
    
    # Grader required if problem is not batch
    grader = (problemType != 'Batch')

    # Stitching takes place for all submissions made in contest mode that are not sent to analysis mirror
    stitch = contestmode.contest() and contestmode.stitch() and contestmode.contestId() != 'analysismirror'

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

    stepFunctionARN = "arn:aws:states:ap-southeast-1:354145626860:stateMachine:Codebreaker-grading-v3"
    res = SFclient.start_execution(stateMachineArn = stepFunctionARN, input = json.dumps(SF_input))

# REGRADE PROBLEM AS INVOKED IN ADMIN PAGE
# Regrade type can be NORMAL, AC, NONZERO
def regradeProblem(problemName, regradeType = 'NORMAL'): 

    # Stitching takes place for all submissions made in contest mode that are not sent to analysis mirror
    stitch = contestmode.contest() and contestmode.stitch() and contestmode.contestId() != 'analysismirror'

    lambda_input = {
        'problemName': problemName,
        'regradeType': regradeType,
        'stitch': stitch
    }

    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-regrade-problem', InvocationType='Event', Payload = json.dumps(lambda_input))   

if __name__ == '__main__':
    # PLEASE KEEP THIS AT THE BOTTOM
    # THIS IS FOR DEBUGGING AND WILL ONLY BE ACTIVATED IF YOU DIRECTLY RUN THIS FILE
    # IT DOES NOT OUTPUT ANYTHING ONTO TMUX
    print(getSubsPerDay())
    pass
