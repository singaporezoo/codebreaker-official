import awstools

#change this
def contest():
    return True
    return False

#change this
def contestId():
    #return 'analysismirror' #remove during contests, to save money
    userinfo = awstools.getCurrentUserInfo()
    if userinfo == None:
        return 'analysismirror'
    username = userinfo['username']
    if username in ['InternetPerson10', 'DippleThree', 'QuantumK9', 'pwned', 'huajun', 'BJoozz', 'SaoST', 'spepd', 'thenymphsofdelphi', 'Ausp3x', 'singaporezoo']:
        return 'practicecontest'
    #if username in ['hhh', 'maomao90', 'zaneyu', 'errorgorn', 'tqbfjotld', 'joelau', 'dantoh', 'rs', 'ryangohca', 'zengminghao', 'myrcella']
    return 'analysismirror'

#change this
def contestIds():
    return ['practicecontest']

def contestproblems():
    problems = ['kmxorm', 'wabot2', 'travelling']
    for i in contestIds():
        problems += awstools.getContestInfo(i)['problems']
    return problems

def fullfeedback():
    return True
    #return False

# show time and memory info
def hidetime():
    #return True
    return False

def cppref():
    return True
    return False

def stitch():
    #return False
    return True

# people who can see subs
def allowedusers():
    return ['zscoder', 'kevinsogo', 'bensonlzl', 'ramapang', 'ace']

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
