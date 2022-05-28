# Modified version of cmp comparison function
# Strips whitespaces and newlines
# Orange, 2020

_WHITES = [' ', '\t', '\n', '\x0b', '\x0c', '\r', '\n']

def _white_diff_canonicalize(string):
    """Convert the input string to a canonical form for the white diff
    algorithm; that is, the strings a and b are mapped to the same
    string by _white_diff_canonicalize() if and only if they have to be
    considered equivalent for the purposes of the white-diff
    algorithm.

    More specifically, this function strips all the leading and
    trailing whitespaces from s and collapse all the runs of
    consecutive whitespaces into just one copy of one specific
    whitespace.

    string (str): the string to canonicalize.
    return (str): the canonicalized string.

    """
    # Replace all the whitespaces with copies of " ", making the rest
    # of the algorithm simpler
    for char in _WHITES[1:]:
        string = string.replace(char, _WHITES[0])

    # Split the string according to " ", filter out empty tokens and
    # join again the string using just one copy of the first
    # whitespace; this way, runs of more than one whitespaces are
    # collapsed into just one copy.
    string = _WHITES[0].join([x for x in string.split(_WHITES[0])
                              if len(x) > 0])
    return string


def _white_diff(output, res):
    """Compare the two output files. Two files are equal if for every
    integer i, line i of first file is equal to line i of second
    file. Two lines are equal if they differ only by number or type of
    whitespaces.

    Note that trailing lines composed only of whitespaces don't change
    the 'equality' of the two files. Note also that by line we mean
    'sequence of characters ending with \n or EOF and beginning right
    after BOF or \n'. In particular, every line has *at most* one \n.

    output (file): the first file to compare.
    res (file): the second file to compare.
    return (bool): True if the two file are equal as explained above.

    """
    
    try:
        lout = output.read()
    except UnicodeDecodeError:
        return False
    lres = res.read()

    # Both files finished: comparison succeded
    if len(lres) == 0 and len(lout) == 0:
        return True

    # Only one file finished: ok if the other contains only blanks
    elif len(lres) == 0 or len(lout) == 0:
        lout = lout.strip(''.join(_WHITES))
        lres = lres.strip(''.join(_WHITES))
        if len(lout) > 0 or len(lres) > 0:
            return False

    # Both file still have lines to go: ok if they agree except
    # for the number of whitespaces
    else:
        lout = _white_diff_canonicalize(lout)
        lres = _white_diff_canonicalize(lres)
        if lout != lres:
            return False
            
    return True


def white_diff_fobj_step(output_fobj, correct_output_fobj):
    """Compare user output and correct output with a simple diff.

    It gives an outcome 1.0 if the output and the reference output are
    identical (or differ just by white spaces) and 0.0 if they don't. Calling
    this function means that the output file exists.

    output_fobj (fileobj): file for the user output, opened in binary mode.
    correct_output_fobj (fileobj): file for the correct output, opened in
        binary mode.

    return ((float, [str])): the outcome as above and a description text.

    """
    if _white_diff(output_fobj, correct_output_fobj):
        return 100
    else:
        return 0


def white_diff_step(output_filename, correct_output_filename):
    """Compare user output and correct output with a simple diff.

    It gives an outcome 1.0 if the output and the reference output are
    identical (or differ just by white spaces) and 0.0 if they don't (or if
    the output doesn't exist).

    sandbox (Sandbox): the sandbox we consider.
    output_filename (str): the filename of user's output in the sandbox.
    correct_output_filename (str): the same with reference output.

    return ((float, [str])): the outcome as above and a description text.

    """
    with open(output_filename,"r") as out_file, \
    	open(correct_output_filename,"r") as res_file:
        return white_diff_fobj_step(out_file, res_file)

