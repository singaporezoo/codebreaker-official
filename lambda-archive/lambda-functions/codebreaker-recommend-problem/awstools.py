import os
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr

judgeName = os.environ['judgeName']

dynamodb = boto3.resource('dynamodb','ap-southeast-1')
users_table=dynamodb.Table(f'{judgeName}-users')
problems_table = dynamodb.Table(f'{judgeName}-problems')

def getUsersTable():

	resp = users_table.scan(ProjectionExpression='username, problemScores')
	val = resp['Items']
	
	while 'LastEvaluatedKey' in resp:
		resp = users_table.scan(ExclusiveStartKey=resp['LastEvaluatedKey'],ProjectionExpression='username, problemScores')
		users = resp['Items']
		val = val.update(users)

	p =getAllProblemsLimited()
	for t in val:
		bad = []
		for x in t['problemScores']:
			try:
				r = p[x]
			except KeyError:
				bad.append(x)
		for i in bad:
			t['problemScores'].pop(i)
	return val

def getAllProblemsLimited():
    res = problems_table.scan(
        ProjectionExpression = 'problemName, analysisVisible, noACs'
    )['Items']
    x = {}
    for i in res:
    	x[i['problemName']] = {
            'analysisVisible':i['analysisVisible'],
            'noAC': i['noACs']
        }
    return x

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
        'problemScores':{},
    }

    return placeHolder