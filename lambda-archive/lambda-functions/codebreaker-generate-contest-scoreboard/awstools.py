import boto3
import json
import subprocess
import time
import random
from pprint import pprint
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from botocore.client import Config
from boto3.dynamodb.conditions import Key, Attr

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table('codebreaker-submissions')
contests_table = dynamodb.Table('codebreaker-contests')
problems_table = dynamodb.Table('codebreaker-problems')
SCOREBOARDS_BUCKET_NAME = 'codebreaker-contest-static-scoreboards'

def getProblemInfo(problemName):
    response= problems_table.query(
        ProjectionExpression = 'subtaskScores,subtaskDependency,testcaseCount',
        KeyConditionExpression = Key('problemName').eq(problemName)
    )
    problem_info=response['Items']
    if len(problem_info) == 0:
        return "This problem doesn't exist"
    if len(problem_info) != 1:
        return "This problem doesn't exist22"

    problem_info = problem_info[0]
    return problem_info


def getSubmissionsListProblem(problem): # Problem
    response = submissions_table.query(
        IndexName = 'problemIndex2',
        KeyConditionExpression=Key('problemName').eq(problem),
        ProjectionExpression = 'score, submissionTime, totalScore, username'
    )
    return response['Items']

def getSubmission(subId, full=True):
    try:
        if full:
            response= submissions_table.get_item( Key={ "subId": subId } )
        else:
            response = submissions_table.get_item( 
                Key={"subId": subId },
                ProjectionExpression = 'subId, maxMemory, maxTime, problemName, submissionTime, totalScore, username'
            )
        subDetails = response['Item']
    
        cppfile = s3.get_object(Bucket=CODE_BUCKET_NAME, Key=f'source/{subId}.cpp')
        code = cppfile['Body'].read().decode("utf-8")
        subDetails['code'] = code

        return subDetails
    except KeyError:
        return None

def getContestInfo(contestId):
    response= contests_table.query(
        ProjectionExpression = '#u,endTime,startTime,problems',
        ExpressionAttributeNames = {'#u':'users'},
        KeyConditionExpression = Key('contestId').eq(contestId)
    )
    contest_info=response['Items']
    if len(contest_info) == 0:
        return None
    return contest_info[0]

def scoreboardUpload(path):
    s3.meta.client.upload_file(path,SCOREBOARDS_BUCKET_NAME,path) 
