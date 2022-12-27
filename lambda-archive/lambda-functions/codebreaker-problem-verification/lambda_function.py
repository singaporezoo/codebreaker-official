import os
import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

judgeName = os.environ['judgeName']
stsclient = boto3.client('sts')
accountId = stsclient.get_caller_identity()['Account'] # Gets account Id programatically

s3=boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
problems_table = dynamodb.Table(f'{judgeName}-problems')

STATEMENTS = f'{judgeName}-statements'
CHECKERS = f'{judgeName}-checkers'
ATTACHMENTS = f'{judgeName}-attachments'
GRADERS = f'{judgeName}-graders'
testdata_bucket = s3.Bucket(f'{judgeName}-testdata')
lambda_client = boto3.client('lambda')

def updateCountLambda(problemName):
    lambda_input = {"problemName": problemName}
    res = lambda_client.invoke(FunctionName = f'arn:aws:lambda:ap-southeast-1:{accountId}:function:{judgeName}-update-testcaseCount', InvocationType='RequestResponse', Payload = json.dumps(lambda_input))

def verifyDependency(dependency,memo):
    ranges = dependency.split(',')
    ans = 0
    for i in ranges:
        nums = i.split('-')
        if len(nums) > 1:
            x, y = int(nums[0]), int(nums[1])
            for i in range(x,y+1):memo[i]=1
            ans=max(ans,y)
        else:
            x = int(nums[0])
            ans=max(ans,x)
            memo[x]=1
            
    return ans

def lambda_handler(event, context):

    problemName = event['problemName']
    updateCountLambda(problemName)
    
    # TODO implement
    remarks= {
        'testdata': 'ok',
        'attachments': 'ok, no attachments required',
        'checker': 'ok, no checker required',
        'statement': 'ok',
        'grader': 'ok, no grader required',
        'subtasks': 'ok',
        'scoring': 'ok'
    }
    verdicts={
        'testdata': 1,
        'attachments' : 1,
        'checker': 1,
        'statement': 1,
        'grader': 1,
        'subtasks': 1,
        'scoring': 1
    }
    response= problems_table.query(
        KeyConditionExpression = Key('problemName').eq(problemName)
    )
    problem_info=response['Items'][0]
    
    # Verifying statements
    hasHTML = True
    hasPDF = True
    try:
        s3.Object(STATEMENTS, f'{problemName}.html').load()
    except ClientError as e:
        hasHTML = False
    
    try:
        s3.Object(STATEMENTS, f'{problemName}.pdf').load()
    except ClientError as e:
        hasPDF = False
    
    if hasHTML and hasPDF:
        remarks['statement'] = 'ok, Both PDF and HTML statements found!'
    elif hasHTML:
        remarks['statement'] = 'ok, HTML statement found!'
    elif hasPDF:
        remarks['statement'] = 'ok, PDF statement found!'
    else:
        remarks['statement'] = 'No statement found!'
        verdicts['statement'] = 0
    
    # Verifying checker
    if problem_info['customChecker'] == 1:
        try:
            s3.Object(CHECKERS, f'compiled/{problemName}').load()
            remarks['checker'] = 'ok, checker found!'
        except ClientError as e:
            remarks['checker'] = 'No checker found!'
            verdicts['checker'] = 0
        
    # Verifying attachments
    if problem_info['attachments'] == 1:
        try:
            s3.Object(ATTACHMENTS, f'{problemName}.zip').load()
            remarks['attachments'] = 'ok, attachments found!'
        except ClientError as e:
            remarks['attachments'] = 'No attachments found!'
            verdicts['attachments'] = 0
        
    # Verifying grader
    if problem_info['problem_type'] != 'Batch':
        hasHeader = True
        hasGrader = True
        try:
            s3.Object(GRADERS, f'{problemName}/grader.cpp').load()
        except ClientError as e:
            hasGrader = False
        
        if problem_info['problem_type'] == 'Interactive':
            try:
                s3.Object(GRADERS, f'{problemName}/{problemName}.h').load()
            except ClientError as e:
                hasHeader = False
        
        else:
            try:
                s3.Object(GRADERS, f"{problemName}/{problem_info['nameA']}.h").load()
                s3.Object(GRADERS, f"{problemName}/{problem_info['nameB']}.h").load()
            except ClientError as e:
                hasHeader = False
        
        if hasGrader and hasHeader:
            remarks['grader'] = 'ok, both header and grader file found!'
        elif hasGrader:
            remarks['grader'] = 'No header file found!'
            verdicts['grader'] = 0
        elif hasHeader:
            remarks['grader'] = 'No grader found!'
            verdicts['grader'] = 0
        else:
            remarks['grader'] = 'No grader and header file found!'
            verdicts['grader'] = 0
    
    # Checking score
    totalScore = 0 
    remarks['scoring'] = f'ok, total score is 100!'
    for i in problem_info['subtaskScores']:
        if i < 0:
            remarks['scoring'] = f'Subtask score cannot be negative!'
            verdicts['scoring'] = 0
        totalScore += i
    if totalScore != 100:
        remarks['scoring'] = f'Total Score is {totalScore}!'
        verdicts['scoring'] = 0
        
    # Checking subtasks
    testcaseCount = int(problem_info['testcaseCount'])
    maxValue = 0
    memo = [0 for i in range(max(testcaseCount+1,2000))]
    for i in problem_info['subtaskDependency']:
        maxValue = max(maxValue,verifyDependency(i,memo))
    if maxValue > testcaseCount:
        remarks['subtasks'] = f'Subtasks reflect {maxValue} testcases while there are {testcaseCount} testcases!'
        verdicts['subtasks'] = 0
    elif sum(memo) != testcaseCount:
        fail = -1
        for i in range(1,testcaseCount+1):
            if not memo[i]: 
                fail = i
                break
        remarks['subtasks'] = f'Testcase {fail} not in any subtask!'
        verdicts['subtasks'] = 0
    
    # Checking testdata
    validation = [[0,0] for i in range(testcaseCount)]
    firstFail = ''
    numFail = 0
    tx = 0
    
    for obj in testdata_bucket.objects.filter(Prefix=f'{problemName}/'):
        print(obj)
        tx += 1
        filename = obj.key
        x = filename.split('/')[1].split('.')
        if x[0] == '':
            continue
        ind = int(x[0])-1
        if ind>=testcaseCount:continue
        if(x[1] == 'in'):
            validation[ind][0]=1
        else:
            validation[ind][1]=1
            
    for i in range(testcaseCount):
        if validation[i][0] == 0:
            if numFail == 0:
                firstFail = f'{i+1}.in'
            numFail += 1
        if validation[i][1] == 0:
            if numFail == 0:
                firstFail = f'{i+1}.out'
            numFail += 1
            
    if numFail:
        verdicts['testdata'] = 0
        remarks['testdata'] = f'{numFail} testcases missing, including file {firstFail}!'
    else:
        remarks['testdata'] = f'ok, {testcaseCount} testcases found!'
        
    complete = 1
    for i in verdicts.keys():
        if verdicts[i] != 1: complete = 0
    
    problems_table.update_item(
        Key = {'problemName':problemName},
        UpdateExpression = f'set validated=:a,verdicts=:b,remarks=:c',
        ExpressionAttributeValues={':a':complete,':b':verdicts,':c':remarks}
        # ExpressionAttributeNames={'#b':'testcaseCount'}
    )
        
    return {
        'statusCode':200,
        'verdicts':verdicts,
        'remarks':remarks
    }

