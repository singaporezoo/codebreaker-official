from flask import render_template, session, request, redirect, flash
import awstools
from datetime import datetime, timedelta

minutesAllowedToReset = 15 #in minutes

def changeemail():
    changeEmailKey = request.args.get('key')
    olduser = request.args.get('olduser')
    userinfo = awstools.getUserInfoFromUsername(olduser)
    
    if changeEmailKey == None or 'changeEmailKey' not in userinfo:
        return redirect("/editprofile")

    if userinfo['changeEmailKey'] == changeEmailKey:
        timeOfGeneration = datetime.strptime(userinfo['timeOfGeneration'], "%Y-%m-%d %X")
        now = datetime.now()

        diffInTime = (now - timeOfGeneration).total_seconds()
        if diffInTime <= minutesAllowedToReset*60:
            awstools.changeEmail(userinfo)
            
            #force logout without the logout page
            for key in list(session.keys()):
                session.pop(key)

            flash("Email Changed Successfully! You may login now", "success")
            
            return redirect("/")
        else:
            flash("The change email link has expired!", "warning")
            return redirect("/editprofile")

    return redirect("/editprofile")
