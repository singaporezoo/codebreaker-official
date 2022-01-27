from flask import flash, render_template, session, request, redirect
from forms import updateAnnouncementForm
import awstools, contestmode
def editannounce(announceId):
    userInfo = awstools.getCurrentUserInfo()
    if userInfo == None or (userInfo['role'] != 'admin' and userInfo['role'] != 'superadmin'):
        flash("Admin access is required", "warning")
        return redirect("/")
    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")
    info = awstools.getAnnounceWithId(announceId)
    if (type(info) is str):
        return 'Sorry, this announcement does not exist'
    form = updateAnnouncementForm()
    if form.is_submitted():
        result = request.form
        inf = {}
        inf['visible'] = ('announce_visible' in result)
        inf['adminOnly'] = ('announce_admin_only' in result)
        inf['priority'] = info['priority']
        inf['aTitle'] = result['announce_name']
        inf['aSummary'] = result['announce_summary']
        inf['aText'] = result['announce_text']
        inf['contestLink'] = result['announce_link']
        awstools.updateAnnounce(announceId, inf)
        return redirect(f'/admin/editannouncement/{announceId}')
    
    return render_template('editannounce.html', form=form, info=info, userinfo=userInfo, contest=contestmode.contest(), socket=contestmode.socket())
