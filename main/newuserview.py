from flask import flash, render_template, session, request, redirect
import awstools
import sendemail,contestmode
from forms import NewUserForm

def newuser():
    userinfo = awstools.getCurrentUserInfo()
    if userinfo == None:
        return 'please login first'
    if userinfo['username'] != '':
        return redirect('/') 
    form = NewUserForm()
    
    if form.is_submitted():
        result = request.form
        username = result['username']
        name = result['name']
        school = result['school']
        email = userinfo['email']

        #check if username exists
        checkUser = awstools.getUserInfoFromUsername(username)
        if checkUser['username'] != '':
            awstools.updateUserInfo(email, '', name, school, 'light', 218)
            flash("This username is taken. Please choose another :<", "warning")
            return redirect('/newuser')
        
        #if userinfo['username'] != '':
            #return redirect('/')

        awstools.updateUserInfo(email, username, name, school, 'light', 218)

        sendemail.sendEmail(awstools.getUserInfo(email), sendemail.ACCOUNT_CREATED)

        return redirect('/')
        
    return render_template('newuser.html', form = form, userinfo=userinfo, socket=contestmode.socket())
