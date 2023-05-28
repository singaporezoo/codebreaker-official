import boto3
dynamodb = boto3.resource('dynamodb')

# Scanning dynamoDB for all elements, and continues until table end using exclusive start key
def scan(table, ProjectionExpression=None, ExpressionAttributeNames = None, ExpressionAttributeValues = None):
    results = []
    if ProjectionExpression == None:
        # No Expression Attribute Names
        resp = table.scan()
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']
    elif ExpressionAttributeNames != None and ExpressionAttributeValues != None:
        resp = table.scan(
            ProjectionExpression=ProjectionExpression,
            ExpressionAttributeNames = ExpressionAttributeNames,
            ExpressionAttributeValues = ExpressionAttributeValues
        )
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ProjectionExpression=ProjectionExpression,
                ExpressionAttributeNames = ExpressionAttributeNames,
                ExpressionAttributeValues = ExpressionAttributeValues,
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']
    elif ExpressionAttributeNames != None:
        resp = table.scan(
            ProjectionExpression=ProjectionExpression,
            ExpressionAttributeNames = ExpressionAttributeNames,
        )
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ProjectionExpression=ProjectionExpression,
                ExpressionAttributeNames = ExpressionAttributeNames,
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']
    elif ExpressionAttributeValues != None:
        resp = table.scan(
            ProjectionExpression=ProjectionExpression,
            ExpressionAttributeValues = ExpressionAttributeValues
        )
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ProjectionExpression=ProjectionExpression,
                ExpressionAttributeValues = ExpressionAttributeValues,
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']
    else:
        resp = table.scan(
            ProjectionExpression=ProjectionExpression,
        )
        results = results + resp['Items']
        while 'LastEvaluatedKey' in resp:
            resp = table.scan(
                ProjectionExpression=ProjectionExpression,
                ExclusiveStartKey = resp['LastEvaluatedKey']
            )
            results = results + resp['Items']
    return results

# helper function for batch get items: 
# If you request more than 100 items, BatchGetItem returns a ValidationException with the message "Too many items requested for the BatchGetItem call."
# From https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.batch_get_item
def batchGetItems (tableName, items, primaryKeyName):
    keys = [{primaryKeyName: i} for i in items]
    # Buckets keys into blocks of size 100
    BLOCK_SIZE = 100
    buckets = [keys[i: i+BLOCK_SIZE] for i in range(0, len(keys), BLOCK_SIZE)]

    results = []
    for bucket in buckets:
        response = dynamodb.batch_get_item( 
            RequestItems = { 
                tableName: { 
                    'Keys': bucket
                }
            }
        )['Responses'][tableName] 
        results += response

    return results