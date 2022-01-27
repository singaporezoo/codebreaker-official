from flask import render_template, session, request, redirect, flash
import awstools
import contestmode

def credits():
    if contestmode.contest():
        flash('Sorry, you cannot view that resource in contest mode', 'warning')
        return redirect(f'/contest/{contestmode.contestId()}')

    return render_template('credits.html',userinfo=awstools.getCurrentUserInfo(),statistics=awstools.credits_page(), socket=contestmode.socket())



