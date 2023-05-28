def getAllContestIds():
    contestIds = scan(contests_table, ProjectionExpression='contestId')
    return contestIds

def getAllGroupIds():
    groupIds = scan(contest_groups_table, ProjectionExpression='groupId')
    return groupIds

def getAllContests():
    return scan(contests_table,
        ProjectionExpression = 'contestId, contestName, startTime, endTime, #a, #b, #c',
        ExpressionAttributeNames={ "#a": "public", "#b" : "duration", '#c':'users' } #not direct cause users is a reserved word
    )

def getAllContestsLimited():
    return scan(contests_table,
        ProjectionExpression = 'contestId, contestName, startTime, endTime, #PUBLIC',
        ExpressionAttributeNames={ "#PUBLIC": "public"} #not direct cause users is a reserved word
    )

def getContestInfo(contestId):
    response= contests_table.query(
        KeyConditionExpression = Key('contestId').eq(contestId)
    )
    contest_info=response['Items']
    if len(contest_info) == 0:
        return None
    return contest_info[0]

def addParticipation(contestId, username):

    if username != "ALLUSERS":
        #change this later
        contests_table.update_item(
            Key = {'contestId' : contestId},
            UpdateExpression = f'set #USERS.#username = :t',
            ExpressionAttributeNames={ "#username": username, "#USERS" : "users" }, #not direct cause users is a reserved word
            ExpressionAttributeValues={ ":t" : datetime.now().strftime("%Y-%m-%d %X") }
        )

    response = contests_table.query(
        KeyConditionExpression = Key('contestId').eq(contestId)
    )
    contest_info=response['Items'][0]
    endTimeStr = contest_info['endTime']
    duration = contest_info['duration']

    if endTimeStr == "Unlimited" and duration == 0:
        return

    if endTimeStr != "Unlimited" and username == "ALLUSERS":
        endTime = datetime.strptime(endTimeStr, "%Y-%m-%d %X") - timedelta(hours = 8)
        scheduleEndParticipation(contestId, username, endTime)
        #cmd = f"echo \"python3 -c 'import awstools; awstools.endParticipation(\\\"{contestId}\\\", \\\"{username}\\\") ' \" | at {endTimeStrAt}"
        return

    stopIndividual = False
    if endTimeStr == "Unlimited":
        stopIndividual = True
        endTime = datetime.now() + timedelta(minutes = int(duration))
    else:
        endTime = datetime.strptime(endTimeStr, "%Y-%m-%d %X") - timedelta(hours = 8)#based on official end Time
        duration = contest_info['duration']
        if duration != 0:
            if endTime > datetime.now() + timedelta(minutes = int(duration)):
                endTime = datetime.now() + timedelta(minutes = int(duration+1))
                stopIndividual = True
            else:
                stopIndividual = False

    endTimeStrAt = endTime.strftime("%H:%M %Y-%m-%d") #for parsing in the at function

    if stopIndividual:
        scheduleEndParticipation(contestId, username, endTime)
    else:
        pass

def scheduleEndParticipation(contestId, username, time):
    if time < datetime.now():
        return
    import app
    app.addEndParticipation(contestId, username, time)

def endParticipation(contestId, username):
    lambda_input = {"contestId":contestId, "username":username}
    res = lambda_client.invoke(FunctionName = 'arn:aws:lambda:ap-southeast-1:354145626860:function:stopcontestwindow', InvocationType='Event', Payload = json.dumps(lambda_input))
