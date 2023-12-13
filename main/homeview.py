from flask import render_template, session, flash, request, redirect
import tags
import awstools
import contestmode
import language
from datetime import datetime, timedelta
from pprint import pprint

def home():
    if contestmode.contest():
        return redirect(f'/contest/{contestmode.contestId()}')

    userinfo = awstools.getCurrentUserInfo()
    if userinfo != None:
        username = userinfo["username"]
    else:
        username = ""
   
    statistics = awstools.homepageInfo()
    contestInfo = statistics['contests']
    if userinfo == None:
        contestInfo = [i for i in contestInfo if i["public"]]
    elif "admin" not in userinfo["role"]:
        contestInfo = [i for i in contestInfo if (i["public"] or userinfo["username"] in i["users"])]

    dates = []
    for i in range(7,0,-1):
        day = datetime.now() - timedelta(days=i)
        dates.append(day.strftime('%d/%m'))
    
    if statistics['pageviews']  == None:
        statistics['pageviews'] = []
    else:
        dates2 = statistics['pageviews'].keys()
        statistics['pageviews'] = [statistics['pageviews'][i] for i in dates2]

    startTour = False
    tour = request.args.get('tour')
    if tour == 'true' and not contestmode.contest():
        startTour = True

    return render_template('home.html',
                           userinfo=userinfo,
                           contestInfo = contestInfo,
                           statistics=statistics,
                           socket=contestmode.socket(),
                           dates=dates,
                           startTour=startTour)


