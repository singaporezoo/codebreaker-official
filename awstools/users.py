def getAllUsers():
    return scan(users_table)

    
def getAllUsernames():
    usernames = scan(users_table,
        ProjectionExpression = 'username'
    )
    return usernames


def getUserInfo(email):
    response = users_table.query(
        KeyConditionExpression = Key('email').eq(email)
    )
    user_info = response['Items']
    if len(user_info) == 0:
        newUserInfo = {
            'email' : email,
            'role' : 'disabled',
            'username' : 'placeholder',
            'theme' : 'alien',
            'problemScores' : {},
            'nation':''
        }
        users_table.put_item(Item = newUserInfo)
        return getUserInfo(email)

    return user_info[0]

def getUserInfoFromUsername(username):
    response = users_table.query(
        IndexName = 'usernameIndex',
        KeyConditionExpression=Key('username').eq(username),
    )
    items = response['Items']
    if len(items) != 0: return items[0]
    return None

def getCurrentUserInfo():
    try:
        email =  dict(session)['profile']['email']
        user_info =  getUserInfo(email)
        return user_info
    except KeyError as e:
        return None
    return None

def updateUserInfo(email, username, fullname, school, theme, hue, nation):
    users_table.update_item(
        Key = {'email' : email},
        UpdateExpression = f'set username =:u, fullname=:f, school =:s, theme =:t, hue=:h, nation=:n',
        ExpressionAttributeValues={':u' : username, ':f' : fullname, ':s' : school, ':t' : theme, ':h':hue, ':n': nation}
    )

def editUserRole(info,newrole,changedby):
    if info['role'] == newrole:
        return

    email = info['email']
    users_table.update_item(
        Key = {'email' : email},
        UpdateExpression = f'set #ts =:r',
        ExpressionAttributeValues={':r' : newrole},
        ExpressionAttributeNames={'#ts':'role'}
    )

    emailType = sendemail.ROLE_CHANGED

    if newrole == 'disabled' or newrole == 'locked':
        emailType = sendemail.ACCOUNT_DISABLED

    if (newrole != 'disabled' and newrole != 'locked') and (info['role'] == 'disabled' or info['role'] == 'locked'):
        emailType = sendemail.ACCOUNT_ENABLED

    sendemail.sendEmail(info,emailType,changedby,newrole)
