import json
import re
import selectors
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

LIMIT = 65536
RUNNER = '''import contextlib, json, runpy, sys
from pathlib import Path
def typed(value):
    if not any(type(value) is allowed for allowed in (type(None), bool, int, float, str, list, tuple, dict)):
        raise TypeError('only exact built-in values are supported')
    name = type(value).__name__
    if type(value) in (list, tuple):
        return [name, [typed(item) for item in value]]
    if type(value) is dict:
        return [name, [[typed(k), typed(v)] for k, v in value.items()]]
    return [name, value]
payload = json.loads(Path('/candidate/input.json').read_text())
try:
    with contextlib.redirect_stdout(sys.stderr):
        function = runpy.run_path('/candidate/answer.py')[payload['function']]
        results = []
        for argument in payload['arguments']:
            actual = function(argument)
            results.append({'actual': typed(actual), 'input_after': typed(argument), 'same_object': actual is argument})
    print(json.dumps({'results': results}, allow_nan=False))
except SyntaxError:
    raise SystemExit(21)
except BaseException:
    raise SystemExit(22)
'''


def exact(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(exact(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(exact(actual[k], expected[k]) for k in expected)
    return actual == expected


def typed(value):
    if not any(type(value) is allowed for allowed in (type(None), bool, int, float, str, list, tuple, dict)):
        raise TypeError('only exact built-in values are supported')
    name = type(value).__name__
    if type(value) in (list, tuple):
        return [name, [typed(item) for item in value]]
    if type(value) is dict:
        return [name, [[typed(k), typed(v)] for k, v in sorted(value.items())]]
    return [name, value]


def normalized(value):
    if type(value) is not list or len(value) != 2:
        raise ValueError('invalid typed observation')
    kind, data = value
    if kind in ('list', 'tuple'):
        return [kind, [normalized(item) for item in data]]
    if kind == 'dict':
        return [kind, sorted([[normalized(k), normalized(v)] for k, v in data])]
    return value


def score(task, stdout):
    try:
        payload = json.loads(stdout)
        if type(payload) is not dict or set(payload) != {'results'}:
            raise ValueError('expected results only')
        results = payload['results']
        if type(results) is not list or len(results) != len(task['cases']):
            raise ValueError('wrong case count')
        passed = 0
        for row, (argument, expected) in zip(results, task['cases']):
            if type(row) is not dict or set(row) != {'actual', 'input_after', 'same_object'} or type(row['same_object']) is not bool:
                raise ValueError('invalid observation')
            passed += (exact(normalized(row['actual']), typed(expected)) and exact(normalized(row['input_after']), typed(argument))
                       and (task['id'] != 'deduplicate' or not row['same_object']))
        return ('pass' if passed == len(results) else 'fail'), passed, ''
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        return 'invalid_output', 0, str(exc)


def extract(answer):
    match = re.fullmatch(r'\s*```(?:python|py)\s*\n(.*?)\n```\s*', answer, re.S)
    return match.group(1) if match and '```' not in match.group(1) else answer


def evaluate(task, answer, image, timeout=4):
    if not re.fullmatch(r'[\w./:-]+@sha256:[0-9a-f]{64}', image):
        raise ValueError('Docker image must be digest-pinned')
    name = 'scm-' + uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix='scm-') as directory:
        path = Path(directory)
        path.chmod(0o755)
        (path / 'answer.py').write_text(extract(answer))
        (path / 'input.json').write_text(json.dumps({'function': task['function'], 'arguments': [c[0] for c in task['cases']]}))
        (path / 'runner.py').write_text(RUNNER)
        for file in path.iterdir():
            file.chmod(0o444)
        command = ['docker', 'run', '--rm', '--pull=never', '--name', name, '--network=none', '--read-only',
                   '--user', '65534:65534', '--cap-drop=ALL', '--security-opt=no-new-privileges',
                   '--pids-limit=32', '--memory=128m', '--memory-swap=128m', '--cpus=0.5',
                   '--mount', f'type=bind,source={path},target=/candidate,readonly',
                   image, 'python', '-I', '-B', '/candidate/runner.py']
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as exc:
            return 'infrastructure_error', 0, str(exc)
        output = bytearray()
        error = bytearray()
        status = None
        deadline = time.monotonic() + timeout
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, output)
        selector.register(process.stderr, selectors.EVENT_READ, error)
        try:
            while selector.get_map():
                if time.monotonic() >= deadline:
                    status = 'timeout'
                    break
                for key, _ in selector.select(0.05):
                    chunk = key.fileobj.read1(4096)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        key.data.extend(chunk)
                if len(output) + len(error) > LIMIT:
                    status = 'output_limit'
                    break
            if status:
                subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=10)
                process.kill()
            process.wait(timeout=10)
        finally:
            selector.close()
            process.stdout.close()
            process.stderr.close()
            subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=10)
        if status:
            return status, 0, status
        if process.returncode:
            status = {21: 'syntax_error', 22: 'runtime_error'}.get(process.returncode, 'runtime_error')
            if process.returncode in (125, 126, 127) and error.startswith(b'docker:'):
                status = 'infrastructure_error'
            return status, 0, error.decode(errors='replace')[:2000]
        return score(task, output.decode(errors='replace'))
