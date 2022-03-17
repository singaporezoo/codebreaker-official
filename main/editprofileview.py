from flask import render_template, session, request, redirect, flash
import awstools
import contestmode
from forms import EditProfileForm

def editprofile():
    userinfo = awstools.getCurrentUserInfo()
    if userinfo == None:
        return 'please login first'
    form = EditProfileForm()

    choices = awstools.themes
    if userinfo['theme'] in choices:
        choices.remove(userinfo['theme'])
    choices.insert(0,userinfo['theme'])
    choices = [s.replace('-',' ').title() for s in choices]

    form.theme.choices = choices

    if form.is_submitted():
        result = request.form
        name = result['name']
        school = result['school']
        theme = result['theme'].lower().replace(' ','-')
        if theme not in awstools.themes:
            flash("Invalid theme!", "warning")
            return redirect('/editprofile')
        if 'hue' in result:
            hue = int(result['hue'])
        else:
            hue = userinfo['hue']
        email = userinfo['email']

        awstools.updateUserInfo(email, userinfo['username'], name, school, theme, hue)
        if theme != userinfo['theme'] and 'custom' in theme:
            return redirect('/editprofile')
        return redirect('/profile/' + userinfo['username'])

    return render_template('editprofile.html', form = form, userinfo=userinfo, contest=contestmode.contest(), users=contestmode.allowedusers(), cppref=contestmode.cppref(), socket=contestmode.socket())
