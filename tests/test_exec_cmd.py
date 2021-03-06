"""Freezer pre_post_exec.py related tests

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This product includes cryptographic software written by Eric Young
(eay@cryptsoft.com). This product includes software written by Tim
Hudson (tjh@cryptsoft.com).
========================================================================

"""




from freezer import  exec_cmd
from mock import patch, Mock
import subprocess


from __builtin__ import True



def test_exec_cmd(monkeypatch):
    cmd="echo test > test.txt"
    popen=patch('freezer.exec_cmd.subprocess.Popen')
    mock_popen=popen.start()
    mock_popen.return_value = Mock()
    mock_popen.return_value.communicate = Mock()
    mock_popen.return_value.communicate.return_value = ['some stderr']
    mock_popen.return_value.returncode = 0
    exec_cmd.execute(cmd)
    assert (mock_popen.call_count == 1)
    mock_popen.assert_called_with(['echo', 'test', '>', 'test.txt'],
                                   shell=False,
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
    popen.stop()


def test__exec_cmd_with_pipe(monkeypatch):
    cmd="echo test|wc -l"
    popen=patch('freezer.exec_cmd.subprocess.Popen')
    mock_popen=popen.start()
    mock_popen.return_value = Mock()
    mock_popen.return_value.communicate = Mock()
    mock_popen.return_value.communicate.return_value = ['some stderr']
    mock_popen.return_value.returncode = 0
    exec_cmd.execute(cmd)
    assert (mock_popen.call_count == 2)
    popen.stop()
