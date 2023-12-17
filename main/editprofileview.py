from flask import render_template, session, request, redirect, flash
import awstools
import contestmode
from forms import EditProfileForm
import sendemail

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
        if 'form_name' in result:
            new_email = request.form.get('new_email')
            new_email = new_email.lower()

            checkingIfNewEmailExists = awstools.getUserInfo(new_email, False)
            if checkingIfNewEmailExists != None:
                flash("A user already is using that email!", "danger")
                return redirect('/editprofile')

            changeEmailKey = awstools.generateChangeEmailKey(userinfo, new_email)

            info = {
                'email' : new_email,
                'name' : userinfo['fullname'],
                'username' : userinfo['username'],
                'oldemail' : userinfo['email'],
                'link' : f"https://codebreaker.xyz/changeemail?key={changeEmailKey}"
            }

            sendemail.sendEmail(info, sendemail.CHANGE_EMAIL)

            flash(f"An email has been sent to {new_email}, please check {new_email}'s inbox for the link to change your email.", "success")
        else:
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
            nation = userinfo['nation']

            awstools.updateUserInfo(email, userinfo['username'], name, school, theme, hue, nation)
            if theme != userinfo['theme'] and 'custom' in theme:
                return redirect('/editprofile')
            return redirect('/profile/' + userinfo['username'])

    return render_template('editprofile.html', form = form, userinfo=userinfo, contest=contestmode.contest(), users=contestmode.allowedusers(), cppref=contestmode.cppref(), socket=contestmode.socket())
