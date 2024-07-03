from flask import render_template, session, url_for, redirect, flash
import awstools, contestmode

def admin():
    # Put this before every admin page lol
    userInfo=awstools.getCurrentUserInfo()
    if userInfo == None or (userInfo['role'] not in ['superadmin', 'admin', 'cmanager']):
        flash("Admin access is required", "warning")
        return redirect("/")
    if contestmode.contest() and (userInfo['role'] != 'superadmin' and userInfo['username'] not in contestmode.allowedusers()):
        flash("You do not have access in contest mode", "warning")
        return redirect("/")

    return render_template('admin.html',userinfo=userInfo, socket=contestmode.socket())

