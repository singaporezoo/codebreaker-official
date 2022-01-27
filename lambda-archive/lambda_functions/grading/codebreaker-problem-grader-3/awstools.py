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
    ML = lambda_input['memoryLimit']
    lambdaML = 128
    if ML <= 128:
        lambdaML = 128
    elif ML <= 256:
        lambdaML = 256
    elif ML <= 512:
        lambdaML = 512
    else:
        lambdaML = 1024
    lambda_input['lambdaML'] = lambdaML
    
    print(lambda_input)
    res = lambda_client.invoke(
        FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:evenmorecringe',
        InvocationType='RequestResponse',
        Payload = json.dumps(lambda_input)
    )

def uploadSubmission(submission_upload):
    submissions_table.put_item(Item = submission_upload)
