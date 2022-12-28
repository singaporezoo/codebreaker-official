import os
import boto3
from pprint import pprint
from boto3.dynamodb.conditions import Key, Attr

judgeName = os.environ['judgeName']
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
submissions_table = dynamodb.Table(f'{judgeName}-submissions')
contests_table = dynamodb.Table(f'{judgeName}-contests')
problems_table = dynamodb.Table(f'{judgeName}-problems')
SCOREBOARDS_BUCKET_NAME = f'{judgeName}-contest-static-scoreboards'

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
        IndexName = 'problemIndex',
        KeyConditionExpression=Key('problemName').eq(problem),
        ProjectionExpression = 'score, submissionTime, totalScore, username'
    )
    return response['Items']

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
