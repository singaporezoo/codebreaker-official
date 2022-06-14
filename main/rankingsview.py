from flask import render_template, session, request, redirect, flash
import awstools
import contestmode

def rankings():
    userinfo = awstools.getCurrentUserInfo()
    if contestmode.contest() and (userinfo == None or userinfo['role'] != 'superadmin'):
        flash('Sorry, you cannot view that resource in contest mode', 'warning')
        return redirect(f'/contest/{contestmode.contestId()}')
    rankings = awstools.getRankings()

    return render_template('rankings.html',userinfo=userinfo,rankings=rankings, socket=contestmode.socket())



