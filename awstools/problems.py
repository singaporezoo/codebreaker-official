
def getAllProblems():
    results = scan(problems_table)
    return results 

def getAllProblemNames():
    problemNames = scan(problems_table, ProjectionExpression = 'problemName')
    return problemNames

# Get limited information for edit problem list
def getAllProblemsLimited():
    return scan(problems_table, 
        ProjectionExpression = 'problemName, analysisVisible, title, #a, author, problem_type, noACs, validated,contestLink,createdTime,tags',
        ExpressionAttributeNames={'#a':'source'}
    )


def validateProblem(problemId):
    lambda_input = {'problemName':problemId}
    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-problem-validation', InvocationType='RequestResponse', Payload = json.dumps(lambda_input))


# Gets list of analysis visible problems for asking clarifications
def getAllProblemsHidden():
    return scan(problems_table,
        ProjectionExpression='problemName, analysisVisible'
    )

def getProblemInfo(problemName):
    response= problems_table.get_item(
    	Key = {'problemName': problemName}
    )
    if 'Item' not in response: return None
    return response['Item']

def updateProblemInfo(problemName, info): 
    problems_table.update_item(
        Key = {'problemName' : problemName},
        UpdateExpression = f'set title=:a, #b=:b, author=:c, problem_type=:d, timeLimit=:e, memoryLimit=:f, fullFeedback=:g, analysisVisible=:h, customChecker=:i,attachments=:j,contestLink=:k,createdTime=:l, editorials=:m, contestUsers=:n',
        ExpressionAttributeValues={':a':info['title'], ':b':info['source'], ':c':info['author'], ':d':info['problem_type'], ':e':info['timeLimit'], ':f':info['memoryLimit'], ':g':info['fullFeedback'], ':h':info['analysisVisible'], ':i':info['customChecker'], ':j':info['attachments'], ':k':info['contestLink'], ':l':info['createdTime'], ':m':info['editorials'],':n':info['contestUsers']},
        ExpressionAttributeNames={'#b':'source'}
    )

def makeAnalysisVisible(problemName):
    problems_table.update_item(
        Key = {'problemName' : problemName},
        UpdateExpression = f'set analysisVisible=:h',
        ExpressionAttributeValues={':h':1},
    )

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
    info['contestUsers'] = []
    info['createdTime'] = (datetime.now() + timedelta(hours=8)).strftime("%Y-%m-%d %X")
    info['editorials'] = []
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

''' BEGIN: PROBLEM FILE MANAGEMENT: '''

# ADMINS CAN DOWNLOAD TESTDATA IN PROBLEM VIEW PAGE
def getTestcase(path):
    tcfile = s3.get_object(Bucket=TESTDATA_BUCKET_NAME, Key=path)
    body = tcfile['Body'].read().decode("utf-8")
    return body

# GET ATTACHMENT IN PROBLEM VIEW PAGE
def getAttachment(path):
    attachment = s3.get_object(Bucket=ATTACHMENTS_BUCKET_NAME, Key=path)
    # No need to decode object because attachments are zip files
    return attachment['Body']

def uploadAttachments(attachments, s3path):
    s3.upload_fileobj(attachments, ATTACHMENTS_BUCKET_NAME, s3path, ExtraArgs={"ContentType":attachments.content_type})

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
    s3.upload_fileobj(statement, STATEMENTS_BUCKET_NAME, s3Name, ExtraArgs={"ContentType":statement.content_type})

def uploadChecker(checker, s3Name):
    s3.upload_fileobj(checker, CHECKERS_BUCKET_NAME, s3Name)

def getChecker(problem_id, path):
    checker = s3.get_object(Bucket=CHECKERS_BUCKET_NAME,Key=f"source/{problem_id}.cpp")
    checker = checker['Body'].read().decode('utf-8')
    with open(path,"w") as f:
        f.write(checker)
        f.close()

def deleteStatement(statementName):
    s3.delete_object(Bucket=STATEMENTS_BUCKET_NAME, Key=statementName)


def uploadCompiledChecker(sourceName, uploadTarget):
    s3.upload_file(sourceName, CHECKERS_BUCKET_NAME, uploadTarget)

def uploadGrader(sourceName, uploadTarget):
    s3.upload_fileobj(sourceName, GRADERS_BUCKET_NAME, uploadTarget)

'''