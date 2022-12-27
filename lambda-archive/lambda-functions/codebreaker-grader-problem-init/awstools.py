import os
import boto3

judgeName = os.environ['judgeName']
dynamodb = boto3.resource('dynamodb','ap-southeast-1')
submissions_table = dynamodb.Table(f'{judgeName}-submissions')

def uploadSubmission(submission_upload):
    submissions_table.put_item(Item = submission_upload)