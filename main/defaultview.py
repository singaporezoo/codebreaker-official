from flask import redirect
import contestmode
def default():
    if contestmode.contest():
        return redirect(f'/contest/{contestmode.contestId()}')
    return redirect('/')
