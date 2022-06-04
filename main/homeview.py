from flask import render_template, session, flash, request, redirect
import tags
import awstools
import contestmode
from datetime import datetime, timedelta

def home():
    if contestmode.contest():
        return redirect(f'/contest/{contestmode.contestId()}')

    userinfo = awstools.getCurrentUserInfo()
    if userinfo != None:
        userSubmissionList = awstools.getSubmissionsList(1, None, userinfo['username'])
        userSubmissionList = userSubmissionList[:8]
    else:
        userSubmissionList = None
    globalSubmissionList = awstools.getSubmissionsList(1, None, None)
    globalSubmissionList = globalSubmissionList[:8]

    if userinfo != None:
        username = userinfo["username"]
    else:
        username = ""
    
    contests = awstools.getAllContests()
    ongoing = []; future = []; past = [];
    for contestinfo in contests:
        if contestinfo["public"] == 0 and not username in contestinfo["users"]:
            continue
        else:
            endTime = contestinfo["endTime"]
            startTime = contestinfo["startTime"]
            duration = contestinfo["duration"]
            if endTime != "Unlimited":
                start = datetime.strptime(startTime, "%Y-%m-%d %X")
                end = datetime.strptime(endTime, "%Y-%m-%d %X")
                now = datetime.now() + timedelta(hours = 8)
                if now < start:
                    future.append(contestinfo)
                elif now > end:
                    past.append(contestinfo)
                else:
                    ongoing.append(contestinfo)
    
    #ongoing.sort(key = lambda x:x['endTime'])
    #future.sort(key = lambda x:x['startTime'])
    #past.sort(key = lambda x:x['endTime'], reverse=True)
    
    def convert(s):
        if s == "Unlimited":
            return 
        s = datetime.strptime(s, "%Y-%m-%d %X").strftime("%d %b %Y %H:%M")
        return s
    for contestlist in [ongoing, future, past]:
        for contest in contestlist:
            contest["startTime"] = convert(contest["startTime"]) 
            contest["endTime"] = convert(contest["endTime"])

    contestInfos = {}
    contestInfos['ongoing'] = ongoing
    contestInfos['future'] = future
    contestInfos['past'] = past

    return render_template('home.html',
                           userinfo=userinfo,
                           globalSubmissionList=globalSubmissionList,
                           userSubmissionList=userSubmissionList,
                           contestInfos=contestInfos,
                           statistics=awstools.credits_page(),
                           socket=contestmode.socket())
