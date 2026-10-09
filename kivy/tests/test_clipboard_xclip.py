"""Linux xclip must not retain a launcher's captured output streams."""
import os
from pathlib import Path
import subprocess
import sys
from shutil import which

import pytest


@pytest.mark.skipif(sys.platform != 'linux', reason='xclip is Linux only')
@pytest.mark.skipif(not os.environ.get('DISPLAY') or not which('xclip'),
                    reason='requires X11 and xclip')
@pytest.mark.parametrize('selection', ['clipboard', 'primary'])
def test_xclip_does_not_hold_parent_output_pipe(selection):
    source = Path(__file__).parents[1] / 'core/clipboard/clipboard_xclip.py'
    child = '''
import importlib.util
import sys
spec = importlib.util.spec_from_file_location('xclip_current', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
clipboard = module.ClipboardXclip()
if sys.argv[2] == 'clipboard':
    clipboard.put(b'clipboard pipe regression')
    assert clipboard.get() == b'clipboard pipe regression'
else:
    clipboard.set_cutbuffer('cutbuffer pipe regression')
    assert clipboard.get_cutbuffer() == 'cutbuffer pipe regression'
print('clipboard round trip completed', flush=True)
'''
    env = dict(os.environ, KIVY_CLIPBOARD='dummy', KIVY_NO_ARGS='1')
    process = subprocess.Popen(
        [sys.executable, '-c', child, str(source), selection],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
    )
    try:
        process.wait(timeout=10)
        assert process.returncode == 0
        output, _ = process.communicate(timeout=1)
        assert b'clipboard round trip completed' in output
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()
