from flask import render_template, session, redirect, request, flash
import awstools, contestmode
from forms import addAnnouncementForm

def editannouncelist():
    userInfo=awstools.getCurrentUserInfo()
    announceInf=awstools.getAllAnnounces()
    if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
        flash("Admin access is required", "warning")
        return redirect("/")
    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")
    form=addAnnouncementForm()
    announceInfl = []
    for info in announceInf:
        announceInfl.append((info['priority'], info))
    announceInfl.sort()
    announceInfl.reverse()
    announceInfo = []
    announcenames = []
    for info in announceInfl:
        announceInfo.append(info[1])
        announcenames.append(info[1]['announceId'])
    if form.is_submitted():
        result = request.form
        if result['announce_id'] == '':
            flash('oopsies! did you accidentally click to add announcements?', 'warning')
            return redirect('/admin/editannouncements')
        if result['announce_id'] in announcenames:
            flash('oopsies! announcement id already taken :(', 'warning')
            return redirect('/admin/editannouncements')
        awstools.createAnnounceWithId(result['announce_id'])
        announce_id = result['announce_id']
        return redirect(f'/admin/editannouncement/{announce_id}')

    return render_template('editannouncelist.html', form=form, userinfo=userInfo, announceinfo=announceInfo, socket=contestmode.socket())

