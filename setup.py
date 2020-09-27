import sys
PYTHON_MINIMUM_VERSION = (3, 6, 0)

if sys.version_info < PYTHON_MINIMUM_VERSION:
    sys.stderr.write("\nKivy requires Python >= %s  detected: %s \n\n", PYTHON_MINIMUM_VERSION, sys.version_info[:3])
    sys.exit(-1)

import subprocess
subprocess.call([sys.executable, 'msetup.py'] + sys.argv[1:])
