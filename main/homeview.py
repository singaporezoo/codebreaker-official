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
    if userinfo != None:
        userSubmissionList = awstools.getSubmissionsList(1, None, userinfo['username'])
        userSubmissionList = userSubmissionList[:8]
    else:
        userSubmissionList = None
    globalSubmissionList = sorted(awstools.getSubmissionsList(1, None, None),key=lambda x:x["subId"], reverse=True)
    globalSubmissionList = globalSubmissionList[:8]

    languages_inverse = language.get_languages_inverse()
    for i in userSubmissionList:
        i['language'] = languages_inverse[i['language']]
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


    dateArr = []
    memo = {}
    for i in range(8):
        date = datetime.now() - timedelta(days=i)
        query = date.strftime('%Y-%m-%d')
        # Looking for the LAST submission of the day
        low = 0 
        high = 200000
        while high > low:
            mid = int((low+high + 1)/2)
            if mid in memo.keys():
                submission = memo[mid]
            else:
                submission = awstools.getSubmission(mid)
                memo[mid] = submission
            if submission != None and query >= submission["submissionTime"]:
                low=mid
            else:
                high=mid - 1
        dateArr.append(low)
    
    dateMap = {}
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        query = date.strftime('%Y-%m-%d')
        dateMap[query] = dateArr[i] - dateArr[i+1]

    credits_info = awstools.credits_page()
    
    #this is slow ><
    """
    lastWeek = datetime.now() - timedelta(days=8)
    weekDate = lastWeek.strftime('%Y-%m-%d')
    # Looking for the LAST submission of the day
    low = 0 
    high = 200000
    while high > low:
        mid = int((low+high + 1)/2)
        if mid in memo.keys():
            submission = memo[mid]
        else:
            submission = awstools.getSubmission(mid)
            memo[mid] = submission
        if submission != None and weekDate >= submission["submissionTime"]:
            low=mid
        else:
            high=mid - 1

    latest = int(awstools.getNumberOfSubmissions())
    submissionList = []
    for i in range(low + 1, latest + 1, 100):
        response = awstools.batchGetSubmissions(i, min(i+100, latest+1)-1)
        submissions = response['Responses']['codebreaker-submissions']
        submissionList += submissions

    dateMap = {}
    problemMap = {}
    for i in submissionList:
        subTime = i['submissionTime']
        date = subTime.strip().split(' ')[0]
        if date not in dateMap:
            dateMap[date] = 0
        dateMap[date] += 1

        problem = i['problemName']
        if problem not in problemMap:
            problemMap[problem] = 0
        problemMap[problem] += 1

    highest = sorted(problemMap, key=problemMap.get, reverse=True)[:5]
    problemMap = dict([(i, problemMap[i]) for i in highest])

    """

    return render_template('home.html',
                           userinfo=userinfo,
                           globalSubmissionList=globalSubmissionList,
                           userSubmissionList=userSubmissionList,
                           contestInfos=contestInfos,
                           statistics=awstools.credits_page(),
                           socket=contestmode.socket())


