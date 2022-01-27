import awstools

#change this
def contest():
    #return True
    return False

#change this
def contestId():
    return 'analysismirror' #remove during contests, to save money
    userinfo = awstools.getCurrentUserInfo()
    if userinfo == None:
        return 'analysismirror'
    username = userinfo['username']
    return 'analysismirror'

#stuff that normal admins cant change
def contestIds():
    return []

def contestproblems():
    problems = []
    for i in contestIds():
        problems += awstools.getContestInfo(i)['problems']
    return problems

def fullfeedback():
    #return True
    return False

def hidetime():
    return True
    return False

def cppref():
    return True
    return False

def stitch():
    #return False
    return True

def allowedusers():
    return []

def socket():
    if not contest():
        return False
    userinfo = awstools.getCurrentUserInfo()
    if userinfo == None:
        return False
    username = userinfo['username']
    role = userinfo['role']
    if username in allowedusers() or role == 'superadmin':
        return True
    return contestId() != 'analysismirror'
