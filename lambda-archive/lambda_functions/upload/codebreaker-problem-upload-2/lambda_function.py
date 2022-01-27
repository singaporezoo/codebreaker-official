from __future__ import print_function
import pickle
import io
import json
import os
from time import sleep
import boto3 # Amazon S3 client library
from googleapiclient.discovery import build # Google drive API service
from googleapiclient.http import MediaIoBaseDownload # Google drive API downloader
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')
problems_table = dynamodb.Table('codebreaker-problems')
BUCKET_NAME = 'codebreaker-testdata' # Name of S3 bucket to upload testdata
rootId = '1YsKMAesnXOfgwMZ_q33E-Mvq2ZQShhVy' # Google drive index of codebreaker testdata
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    problemName = event["problemName"] # Name of problem
    
    creds = None
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

    # Building google drive client
    service = build('drive', 'v3', credentials=creds)

    # Querying for google drive folder with name as the problem name and is located inside the codebreaker-testdata folder
    results = service.files().list(
        q="name = '{0}' and '{1}' in parents".format(problemName,rootId)
    ).execute()

    items = results.get('files', [])

    if len(items) == 0:
        return {
            'statusCode': 300, #Database transaction failed
            'errorMessage': 'Testdata folder not found'
        }

    for folder in items:
        folderId = folder['id']
        
        results = service.files().list(
            pageSize = 1000, q="parents = '{0}'".format(folderId)
        ).execute()
        items = results.get('files', [])
        testcaseCount =len(items)
        z=[0]*(testcaseCount+1)
        problems_table.update_item(
            Key = {'problemName' : problemName},
            UpdateExpression = f'set testcasesUploaded = :st',
            ExpressionAttributeValues = {':st':z}
        )

        indexes = [i['id'] for i in items]
        print(testcaseCount)

        for i in range(1,testcaseCount+1):
            lambda_input={
              "problemName": problemName,
              "fileId": items[i-1]['id'],
              "statusId": i
            }
            # print(lambda_input)
            res = lambda_client.invoke(
                FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:codebreaker-testcase-upload',
                InvocationType='Event',
                Payload = json.dumps(lambda_input)
            )

    return {
        'statusCode':200
    }


if __name__ == '__main__':
    lambda_handler({'problemName':'wiring'}, None)