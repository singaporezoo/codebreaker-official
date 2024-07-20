from flask import render_template, session, flash, redirect
import awstools
import contestmode
from datetime import datetime, timedelta

def scoreboard(contestId):
    if contestId == "analysismirror":
        flash("Sorry, you cannot view the scoreboard for analysis mirror", "warning")
        return redirect("/contest/analysismirror")
    contestinfo = awstools.getContestInfo(contestId)
    userinfo = awstools.getCurrentUserInfo()
    if contestinfo == None:
        return "sorry this page doesn't exist"

    if userinfo == None:
        flash("Sorry, please sign up for an account to view this resource!", "warning")
        return redirect("/contests")
    
    username = userinfo['username']

    if contestinfo["public"] == 0 and not username in contestinfo["users"] and userinfo['role'] != 'superadmin' and username not in contestmode.allowedusers():
        flash("Sorry, you've not been invited to this private contest!", "warning")
        return redirect("/contests")
    
    if not contestinfo["publicScoreboard"] and not userinfo['role'] in ["cmanager", "admin", "superadmin"]:
        flash("Sorry, the scoreboard is not public", "warning")
        return redirect("/contests")
    
    if contestmode.contest() and userinfo['username'] not in contestmode.allowedusers() and userinfo['role'] != 'superadmin':
        flash("Sorry, the scoreboard is not public", "warning")
        return redirect("/contests")
    
    start = datetime.strptime(contestinfo['startTime'], "%Y-%m-%d %X") 
    now = datetime.now() + timedelta(hours = 8)

    past = False
    endTime = contestinfo['endTime']
    if endTime != "Unlimited":
        end = datetime.strptime(endTime, "%Y-%m-%d %X")
        past = (end < now)

    if now < start:
        flash("Sorry, this contest hasn't started yet", "warning")
        return redirect(f"/contests")

    problemNames = contestinfo['problems']
    problems = []
    for P in problemNames:
        t = awstools.getProblemInfo(P)
        if type(t) != str:
            problems.append(t)

    problemInfo = [dict((key,value) for key, value in P.items() if key in ['problemName','analysisVisible','title', 'source', 'author','problem_type','noACs']) for P in problems]
    #userInfo = awstools.getCurrentUserInfo()
	    
    users = contestinfo['users']
    participantInfo = []

    listOfScores = {}
    
    allUsersList = awstools.getAllUsers()
    allUsers = {}
    for user in allUsersList:
        allUsers[user['username']] = user
    
    for user in users:
        totalScore = 0
        status = "Ongoing"

        if user in contestinfo['scores']:
            problemScores = contestinfo['scores'][user]
            status = "Finished"
        else:
            problemScores = allUsers[user]['problemScores']
            timeStarted = users[user]

        for problem in problemNames:
            if problem in problemScores:
                listOfScores[f'{user}+{problem}'] = problemScores[problem]
                totalScore += problemScores[problem]
            else:
                listOfScores[f'{user}+{problem}'] = '-'
        participantInfo.append({"username" : user, "totalScore" : totalScore, "status": status})
    
    participantInfo.sort(key = lambda x : x["totalScore"], reverse=True)
    for i in range(len(participantInfo)):
        if userinfo != None and participantInfo[i]["username"] == userinfo["username"]:
            participantInfo[i]["sameuser"] = True
        if i != 0 and participantInfo[i]["totalScore"] == participantInfo[i-1]["totalScore"]:
            participantInfo[i]["rank"] = participantInfo[i-1]["rank"]
        else:
            participantInfo[i]["rank"] = i+1
            
    return render_template('scoreboard.html', contestinfo=contestinfo, problemNames=problemNames, participantInfo=participantInfo, scores=listOfScores, userinfo=userinfo, contest=contestmode.contest(), users=contestmode.allowedusers(), cppref=contestmode.cppref(), socket=contestmode.socket())
