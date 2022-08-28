from flask import render_template, session, request, redirect, flash
import awstools
import contestmode

def credits():
    userinfo = awstools.getCurrentUserInfo()
    if contestmode.contest() and (userinfo == None or userinfo['role'] != 'superadmin'):
        flash('Sorry, you cannot view that resource in contest mode', 'warning')
        return redirect(f'/contest/{contestmode.contestId()}')

    return render_template('credits.html',userinfo=userinfo,statistics=awstools.homepageInfo(), socket=contestmode.socket())



