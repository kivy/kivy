""" Verification and testing tools for verifying command line results.
It includes associated test harnesses so that other tests can quickly be written.  """

from contextlib import contextmanager
import re
import subprocess as S
import shutil
import os

# Run in shell commands

def run(cmd):
    """ run command, returning tuple of stdout, stderr, and return_code """
    sub = S.Popen(cmd, stdout=S.PIPE, stderr=S.PIPE, shell=True)
    sub_stdout, sub_stderr = sub.communicate()
    return_code = sub.wait()
    return sub_stdout, sub_stderr, return_code

RE_NOTHING = "^$"  # match only an empty string
def run_match(cmd, stdout_regex=None, stdout_contains=None,
              stderr_regex=None, stderr_contains=None, negate=False):
    """
    General version of running a command and checking its output and stdout
    against regex patterns or static text.

    :param cmd:  The command to run in a subshell.  Shell substitutions are ok.
    :param stdout_regex:  The regex that must match the stdout.  None for
       allow anything.  RE_NOTHING if there must be no output.
    :param negate:   Negate the stderr and stdout matching parameters to mean
    'must not match'.  None matching parameters are still ignored.
    :return:   return True if passing.

    """

    def fails_test(failed, message):
        """ if failed, print the message to stdout and then return failed.
        Helpful for understanding why tests fail. """
        if failed:
            print "FAIL: {}\ncommand={}\nstdout={}\nstderr={}\nreturn_code={}".format(message, cmd, o, e, r)
        return failed

    o, e, r = run(cmd)
    fail_basic = (
          fails_test(stdout_regex == RE_NOTHING and o, "stdout not empty")
       or fails_test(stderr_regex == RE_NOTHING and e, "stderr not empty")
       or fails_test(e and r == 0, "return code was 0 but output to stderr")
       or fails_test(not e and r != 0, "return code was not 0 but no output to stderr"))
    if negate:
        fail_matching = (
           fails_test(stdout_regex and stdout_regex != RE_NOTHING and re.search(stdout_regex, o),
               "stdout matched {}".format(stdout_regex))
           or fails_test(stderr_regex and stderr_regex != RE_NOTHING and re.search(stderr_regex, e),
               "stderr matched {}".format(stderr_regex))
           or fails_test(stdout_contains and stdout_contains in o,
               "stdout contained {}".format(stdout_contains))
           or fails_test(stderr_contains and stderr_contains in e,
               "stderr contained {}".format(stderr_contains)))
    else:
        fail_matching = (
            fails_test(stdout_regex and not re.search(stdout_regex, o),
               "stdout did not match {}".format(stdout_regex))
           or fails_test(stderr_regex and not re.search(stderr_regex, e),
               "stderr did not match {}".format(stderr_regex))
           or fails_test(stdout_contains and stdout_contains not in o,
               "stdout did not contain {}".format(stdout_contains))
           or fails_test(stderr_contains and stderr_contains not in e,
               "stderr did not contain {}".format(stderr_contains)))
    return not fail_basic and not fail_matching

def stderr_match(cmd, regex=None, contains=None, negate=False):
    return run_match(cmd, stdout_regex=RE_NOTHING, stderr_regex=regex,
                     stderr_contains=contains, negate=negate)

def stdout_match(cmd, regex=None, contains=None, negate=False):
    """ with no arguments, will still check for empty stdout and error code. """
    return run_match(cmd, stderr_regex=RE_NOTHING, stdout_regex=regex,
                     stdout_contains=contains, negate=negate)

def indent(block, depth=1):
    return "\n".join([("  " * depth + l) for l in block.split("\n")])

def match_check(first_run, o1, e1, r1, second_run, o2, e2, r2):
    def print_it(name, first, second):
        if first == second:
            print "  {} matched:\n{}".format(name, indent(first, 2))
        else:
            print "  {name} differed:\n    First {name}:\n{first}\n    Second {name}:\n{second}\n".format(
                name=name, first=indent(first,4), second=indent(second,4))
    if o1 != o2 or e1 != e2 or r1 != r2:
        print "Failed To Match:"
        print "  command 1:{}".format(first_run)
        print "  command 2:{}".format(second_run)
        print_it("stdout", o1, o2)
        print_it("stderr", e1, e2)
        print_it("return code", str(r1), str(r2))
        return False
    else:
        return True

def match_run(first_run, second_run):
    o1, e1, r1 = run(first_run)
    o2, e2, r2 = run(second_run)
    return match_check(first_run, o1, e1, r1, second_run, o2, e2, r2)


# Sandbox routines
def u(plain_string):
    """ return simple unicode string """
    return plain_string.encode('utf8')

def make_file(name, contents=None):
    """make a file in the current dirctory with given contents,
    or the file name if none."""
    if contents is None:
        contents = "The file is named:{}:".format(u(name))
    with open(name, 'w') as f:
        f.write(contents)

@contextmanager
def in_big_sandbox(subdir='testing_sandbox'):
    with in_sandbox(subdir):
        make_sandbox_files()
        yield

@contextmanager
def in_sandbox(subdir='testing_sandbox'):
    remove_dir(subdir)
    os.mkdir(subdir)
    curdir = os.getcwd()
    os.chdir(subdir)
    yield
    os.chdir(curdir)
    remove_dir(subdir)

def remove_dir(subdir):
    try:
        shutil.rmtree(subdir)
    except OSError:
        pass

def make_sandbox_files():
    """ make sandbox files in current directory """
    make_file('a space in the filename')
    make_file('a return\n or two\n in the filename')
    make_file(u'a plain unicode name')
    make_file(u'a unicode name with ghad \u0542 character')
    make_file('emacs backup 1~')
    make_file('emacs backup 2~')
    make_file('emacs backup 3~')
    make_file('zero-a', "a:R0 L0\nR0 L1\0R1 L0\nR1 L1\n\0R2 L2")
    make_file('zero-b',"b:R0 L0\nb:R0 L1\0b:R1 L0\nb:R1 L1\n\0b:R2 L2")
    make_file('a', 'Hello from file a.')
    make_file('b', 'Hello from file b.')

def test_perl_equivalents():
    assert match_run("""perl -e 'print "Hello\n"'""", """one 'print "Hello"'""")
    assert match_run("""python -m this | perl -pe 's/is better than/exceeds/'""",
                     """python -m this | one -p 'sub("is better than", "exceeds", oL)'""")
    w = """This is   \n a string  \n with whitespace.  \n\n\n"""
    in_w = "<<EOF\n" + w + "\nEOF"
    assert match_run(r"""perl -lpe 's/\s*$//'""" + in_w, """one -p 'oL.rstrip()'""" + in_w)
