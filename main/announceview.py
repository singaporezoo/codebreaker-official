from flask import flash, render_template, session, request, redirect
import awstools
import contestmode
def announce(announceId):
    userInfo = awstools.getCurrentUserInfo()
    info = awstools.getAnnounceWithId(announceId)
    if type(info) is str or not info['visible'] or (info['adminOnly'] and (userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'))):
        flash('Sorry, this announcement does not exist', 'warning')
        return redirect('/announcements')
        
    return render_template('announce.html', info=info, userinfo=userInfo, contest=contestmode.contest(), cppref=contestmode.cppref(), socket=contestmode.socket())
