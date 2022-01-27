import json
import boto3
import datetime
from time import sleep
from math import ceil
from concurrent.futures.thread import ThreadPoolExecutor
from boto3.dynamodb.conditions import Key, Attr
import time
import awstools

dynamodb = boto3.resource('dynamodb','ap-southeast-1')
contests_table = dynamodb.Table('codebreaker-contests')

def lambda_handler(event, context):
    username = event['username']
    contestId = event['contestId']
    
    #userInfo = awstools.getUserInfoFromUsername(username)
    contestinfo = awstools.getContestInfo(contestId)
    #username = userInfo["username"]
    
    usernames = []
    userTable = None
    if event['username'] == "ALLUSERS":
        for user in contestinfo['users']:
            if contestinfo['users'][user] == '0':
                continue
            if user not in contestinfo['scores']:
                usernames.append(user);
        #print(usernames)
    else:
        usernames = [username]
    
    print(userTable);
    
    for username in usernames:
        scores = {}
        userInfo = awstools.getUserInfoFromUsername(username)
        problemNames = contestinfo['problems']
        for problem in problemNames:
            if problem in userInfo["problemScores"]:
                scores[problem] = userInfo["problemScores"][problem]
        
        contests_table.update_item(
            Key = {'contestId' : contestId},
            UpdateExpression = f'set scores.#username = :s',
            ExpressionAttributeNames={ "#username": username }, #not direct cause users is a reserved word
            ExpressionAttributeValues={ ":s" : scores }
        )
    
    return {
        "statusCode":200,
    }