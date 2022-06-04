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
    
    contestInfos = [{'contestName':'dummy','startTime':datetime.now(), 'endTime':datetime.now()+datetime.timedelta(days=1)}]

    return render_template('home.html',
                           userinfo=userinfo,
                           globalSubmissionList=globalSubmissionList,
                           userSubmissionList=userSubmissionList,
                           contestInfos=contestInfos,
                           statistics=awstools.credits_page(),
                           socket=contestmode.socket())
