''' GLOBAL FILE THAT GIVES MAPPING OF LANGUAGES TO SHORT FORMS ''' 

languages = {
    'C++ 17': 'cpp',
    'Python 3': 'py'
}

languages_inverse = {}

for i in languages:
    languages_inverse[languages[i]] = i

def get_languages(): return languages
def get_languages_inverse(): return languages_inverse
