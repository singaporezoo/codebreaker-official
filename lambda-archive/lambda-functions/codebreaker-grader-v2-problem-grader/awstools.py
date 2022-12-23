import boto3

dynamodb = boto3.resource('dynamodb','ap-southeast-1')
submissions_table = dynamodb.Table('codebreaker-submissions')

def uploadSubmission(submission_upload):
    submissions_table.put_item(Item = submission_upload)