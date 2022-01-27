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

def finish(verdict,problemName,statusId):
    problems_table.update_item(
        Key = {'problemName' : problemName},
        UpdateExpression = f'set testcasesUploaded[{statusId}] = :st',
        ExpressionAttributeValues = {':st':verdict}
    )

def lambda_handler(event, context):
    fileId = event['fileId']
    statusId = event['statusId']
    problemName = event['problemName']

    creds = None
    with open('token.pickle','rb') as token:
        creds = pickle.load(token)

    # Building google drive client
    service = build('drive', 'v3', credentials=creds)

    file=None
    try: 
        file = service.files().get(fileId=fileId).execute()
    except: 
        finish(-1,problemName,statusId)
        return {
            'statusCode':300
        }
    filename=file['name']
    print(filename)

    ind = filename.split('.')
    if len(ind) != 2:
        finish(-1,problemName,statusId)
        return {
            'statusCode': 300
        }

    if ind[1] != 'in' and ind[1] != 'out':
        finish(-1,problemName,statusId)
        return {
            'statusCode': 300
        }

    try:
        l = int(ind[0])
    except ValueError:
        finish(-1,problemName,statusId)
        return {
            'statusCode': 300
            # 'errorMessage': 'File Name {0} has invalid index'.format(filename)
        }

    filename = f'{str(int(ind[0]))}.{ind[1]}'

    try:
        request = service.files().get_media(fileId=fileId)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fd=fh, request=request)
        # Downloading file from google drive
        done = False
        while not done:
            status,done = downloader.next_chunk()
    except:
        finish(-1,problemName,statusId)
        return {
            'statusCode': 301 #Database transaction failed
        }

    fh.seek(0)
    lambda_path='/tmp/{0}'.format(filename)

    with open(lambda_path,'wb') as f:
        f.write(fh.read())
        f.close()

    # Pushing file onto AWS S3
    s3path='{0}/{1}'.format(problemName,filename)
    s3.meta.client.upload_file(lambda_path,BUCKET_NAME,s3path) 

    # Clearing download to ensure that lambda does not run into memory issues
    os.remove(lambda_path)

    try:
        # If possible, delete file permentantly
        service.files().delete(fileId=fileId).execute()
        print("Deleted file {0}".format(filename))
    except:
        finish(-1,problemName,statusId)
        return{
            'statusCode':302
        }
    
    finish(1,problemName,statusId)
    return {
        'statusCode': 200
    }
