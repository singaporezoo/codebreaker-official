from flask import render_template, session, request, redirect, flash
import awstools
import contestmode

def rankings():
    if contestmode.contest():
        flash('Sorry, you cannot view that resource in contest mode', 'warning')
        return redirect(f'/contest/{contestmode.contestId()}')
    rankings = awstools.getRankings()

    return render_template('rankings.html',userinfo=awstools.getCurrentUserInfo(),rankings=rankings, socket=contestmode.socket())



