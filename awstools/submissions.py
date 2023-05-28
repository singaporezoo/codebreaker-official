def getSubmission(subId, full=True):
    if full:
        response= submissions_table.get_item( Key={ "subId": subId } )
    else:
        response = submissions_table.get_item( 
            Key={"subId": subId },
            ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, gradingTime, totalScore, username, #l, compileErrorMessage',
            ExpressionAttributeNames = {'#l': 'language'}
        )
    
    if 'Item' not in response.keys(): return None
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


def getNextSubmissionId():
    resp = counters_table.update_item(
    Key = {'counterId': 'submissionId'},
    UpdateExpression = 'ADD #a :x',
    ExpressionAttributeNames = {'#a' : 'value'},
    ExpressionAttributeValues = {':x' : 1},
    ReturnValues = 'UPDATED_NEW'
    )
    subId = int(resp['Attributes']['value'])
    return subId


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
            IndexName = 'usernameIndex',
            KeyConditionExpression=Key('username').eq(username),
            Limit = (pageNo+1)*subPerPage + 2,
            ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, totalScore, username, #a, compileErrorMessage',
            ExpressionAttributeNames = {'#a': 'language'},
            ScanIndexForward = False
        )
        return response['Items']
    elif username == None and problem != None:
        response = submissions_table.query(
            IndexName = 'problemIndex',
            KeyConditionExpression=Key('problemName').eq(problem),
            ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, totalScore, username, #a, compileErrorMessage',
            ExpressionAttributeNames = {'#a': 'language'},
            Limit = (pageNo+1)*subPerPage + 2,
            ScanIndexForward = False
        )
        return response['Items']
    else:
        response = submissions_table.query(
            IndexName = 'problemIndex',
            KeyConditionExpression=Key('problemName').eq(problem),
            ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, totalScore, username, #a, compileErrorMessage',
            ExpressionAttributeNames = {'#a': 'language'},
            FilterExpression = Attr('username').eq(username),
            ScanIndexForward = False
        )
        return response['Items']

def getSubmissionsToProblem(problemName):
    response = submissions_table.query(
        IndexName = 'problemIndex',
        KeyConditionExpression = Key('problemName').eq(problemName),
        ProjectionExpression = 'subId',
        ScanIndexForward = False
    )
    return response['Items']

def getNumberOfSubmissions():
    resp = counters_table.query(
        KeyConditionExpression = Key('counterId').eq('submissionId')
    )
    item = resp['Items'][0]
    subId = int(item['value'])
    return subId
