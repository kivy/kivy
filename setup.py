import sys
PYTHON_MINIMUM_VERSION = (3, 6, 0)

if sys.version_info < PYTHON_MINIMUM_VERSION:
    sys.stderr.write("\nKivy requires Python >= " + str(PYTHON_MINIMUM_VERSION) + ' detected:' + str(sys.version_info[:3]) + ' \n\n')
    sys.exit(-1)

import subprocess
subprocess.call(['python', 'msetup.py'] + sys.argv[1:])
