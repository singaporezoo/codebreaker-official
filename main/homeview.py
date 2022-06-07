from flask import render_template, session, flash, request, redirect
import tags
import awstools
import contestmode
import language
from datetime import datetime, timedelta

def home():
    if contestmode.contest():
        return redirect(f'/contest/{contestmode.contestId()}')

    userinfo = awstools.getCurrentUserInfo()
    languages_inverse = language.get_languages_inverse()
    if userinfo != None:
        userSubmissionList = awstools.getSubmissionsList(1, None, userinfo['username'])
        userSubmissionList = userSubmissionList[:8]
        for i in userSubmissionList:
            i['language'] = languages_inverse[i['language']]
    else:
        userSubmissionList = None
    globalSubmissionList = sorted(awstools.getSubmissionsList(1, None, None),key=lambda x:x["subId"], reverse=True)
    globalSubmissionList = globalSubmissionList[:8]
    for i in globalSubmissionList:
        i['language'] = languages_inverse[i['language']]

    if userinfo != None:
        username = userinfo["username"]
    else:
        username = ""
    
    contestInfos = [i for i in awstools.getAllContests() if i["endTime"] != "Unlimited"]
    if userinfo == None:
        contestInfos = [i for i in contestInfos if i["public"]]
    elif "admin" not in userinfo["role"]:
        contestInfos = [i for i in contestInfos if (i["public"] or userinfo["username"] in i["users"])]


    subsPerDay = awstools.getSubsPerDay()
    credits_info = awstools.credits_page()

    return render_template('home.html',
                           userinfo=userinfo,
                           globalSubmissionList=globalSubmissionList,
                           userSubmissionList=userSubmissionList,
                           contestInfos=contestInfos,
                           statistics=awstools.credits_page(),
                           socket=contestmode.socket(),
                           subsPerDay=subsPerDay)


