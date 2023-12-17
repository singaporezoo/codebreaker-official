from flask import render_template, session, request, redirect, flash
import awstools
from datetime import datetime, timedelta

minutesAllowedToReset = 15 #in minutes

def changeemail():
    userinfo = awstools.getCurrentUserInfo()
    changeEmailKey = request.args.get('key')

    if changeEmailKey == None or 'changeEmailKey' not in userinfo:
        return redirect("/editprofile")


    if userinfo['changeEmailKey'] == changeEmailKey:
        timeOfGeneration = datetime.strptime(userinfo['timeOfGeneration'], "%Y-%m-%d %X")
        now = datetime.now()

        diffInTime = (now - timeOfGeneration).total_seconds()
        if diffInTime <= minutesAllowedToReset*60:
            awstools.changeEmail(userinfo)
            flash("Email Changed Successfully!", "success")
            return redirect("/logout")
        else:
            flash("The change email link has expired!", "warning")
            return redirect("/editprofile")
    return changeEmailKey
