from flask import render_template, session, redirect
import awstools
import contestmode

def profile(username):    
    profileinfo = awstools.getUserInfoFromUsername(username)
    superhidden = awstools.getSuperhiddenProblems()

    if profileinfo['username'] == "":
        return "Sorry this user doesn't exist"

    if 'nation' not in profileinfo.keys():
        profileinfo['nation'] = 'N/A'

    columns = [ [], [], [], [] ]

    cnt = 0

    problems = []
    for problem, score in profileinfo['problemScores'].items():
        if score != 100:
            continue
        if problem in superhidden:
            continue
        problems.append(problem)

    problems.sort()

    for problem in problems:
        columns[cnt%4].append(problem)
        cnt += 1

    while cnt % 4 != 0:
        columns[cnt%4].append("");
        cnt += 1;

    solvedproblems = []
    for i in range(len(columns[0])):
        curSet = {}
        curSet['col1'] = columns[0][i]
        curSet['col2'] = columns[1][i]
        curSet['col3'] = columns[2][i]
        curSet['col4'] = columns[3][i]
        solvedproblems.append(curSet)
    
    if contestmode.contest():
        solvedproblems = []

    return render_template('profile.html', profileinfo=profileinfo, solvedproblems=solvedproblems, userinfo=awstools.getCurrentUserInfo(), contest=contestmode.contest(), users=contestmode.allowedusers(), cppref=contestmode.cppref(), socket=contestmode.socket())

