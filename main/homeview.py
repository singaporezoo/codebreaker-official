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
    globalSubmissionList = sorted(awstools.getSubmissionsList(1, None, None),key=lambda x:x["subId"], reverse=True)
    globalSubmissionList = globalSubmissionList[:8]



    if userinfo != None:
        username = userinfo["username"]
    else:
        username = ""
    
    contestInfos = [i for i in awstools.getAllContests() if i["endTime"] != "Unlimited"]
    if userinfo == None:
        contestInfos = [i for i in contestInfos if i["public"]]
    elif "admin" not in userinfo["role"]:
        contestInfos = [i for i in contestInfos if (i["public"] or userinfo["username"] in i["users"])]



    lastWeek = datetime.datetime.now() - datetime.timedelta(days=7)
    weekDate = lastWeek.strftime('%Y-%m-%d')
    # Looking for the LAST submission of the day
    low = 0 
    high = 200000
    while high > low:
        mid = int((low+high + 1)/2)
        submissionTime = awstools.getSubmission(mid)['submissionTime']
        if query >= submissionTime:
            low=mid
        else:
            high=mid - 1
    print(low)
    

    return render_template('home.html',
                           userinfo=userinfo,
                           globalSubmissionList=globalSubmissionList,
                           userSubmissionList=userSubmissionList,
                           contestInfos=contestInfos,
                           statistics=awstools.credits_page(),
                           socket=contestmode.socket())


