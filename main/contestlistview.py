from flask import render_template, session, flash, redirect
import awstools
import contestmode
from datetime import datetime, timedelta
from forms import beginContestForm

def contestlist():
    contests = awstools.getAllContests()
    
    if contestmode.contest():
        flash('Sorry, you cannot view that resource in contest mode', 'warning')
        return redirect(f'/contest/{contestmode.contestId()}')

    shownContests = []
    
    userInfo = awstools.getCurrentUserInfo()
    
    if userInfo == None:
        flash("Please login to view this page", "warning")
        return redirect("/")

    username = userInfo["username"]
    
    ongoing = []; future = []; past = []; timedPractice = []; collections = [];
    for contestinfo in contests:
        if contestinfo["public"] == 0 and not username in contestinfo["users"]:
            continue
        else:
            endTime = contestinfo["endTime"]
            startTime = contestinfo["startTime"]
            duration = contestinfo["duration"]
            #if contestinfo["contestId"] == "starterproblems":
                #print(contestinfo)
            if endTime == "Unlimited":
                if duration == 0:
                    collections.append(contestinfo)
                else:
                    timedPractice.append(contestinfo)
            else:
                start = datetime.strptime(startTime, "%Y-%m-%d %X")
                end = datetime.strptime(endTime, "%Y-%m-%d %X")
                now = datetime.now() + timedelta(hours = 8)
                if now < start:
                    future.append(contestinfo)
                elif now > end:
                    past.append(contestinfo)
                else:
                    ongoing.append(contestinfo)
    
    ongoing.sort(key = lambda x:x['endTime'])
    future.sort(key = lambda x:x['startTime'])
    past.sort(key = lambda x:x['endTime'], reverse=True)
    timedPractice.sort(key = lambda x:x['contestName'])
    collections.sort(key = lambda x:x['startTime'], reverse=True)
    
    def convert(s):
        if s == "Unlimited":
            return 
        s = datetime.strptime(s, "%Y-%m-%d %X").strftime("%d %b %Y %H:%M")
        return s
    for contestlist in [ongoing, future, past, timedPractice, collections]:
        for contest in contestlist:
            contest["startTime"] = convert(contest["startTime"]) 
            contest["endTime"] = convert(contest["endTime"]) 
    
    contestInfos = {}
    contestInfos['ongoing'] = ongoing
    contestInfos['future'] = future
    contestInfos['past'] = past
    contestInfos['timedPractice'] = timedPractice
    contestInfos['collections'] = collections
    contestGroupsInfo = awstools.getAllContestGroups()
    contestGroupsInfo = [i for i in contestGroupsInfo if i['visible'] == 1]
    contestGroupsInfo.sort(key = lambda x:x['groupName'])

    havecurrent = (len(contestInfos['ongoing']) > 0)

    return render_template('contestlist.html', contestInfos = contestInfos, havecurrent=havecurrent, userinfo=userInfo, contestgroupsinfo=contestGroupsInfo, users=contestmode.allowedusers(), socket=contestmode.socket())
