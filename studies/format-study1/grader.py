"""Offline Docker grading. Expected answers remain in the host process."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
IMAGE = 'python:3.12-slim@sha256:cb33f7f771ecec2ef1225cf39b159591a040391bd73e4c01f00fdfc4c47611d2'
TIMEOUT = 10
OUTPUT_LIMIT = 1024 * 1024

def matches(actual, expected):
    return actual.split() == expected.split()

def run_case(code, stdin):
    with tempfile.TemporaryDirectory(prefix='format-study-case-') as folder:
        sandbox = Path(folder)
        (sandbox / 'main.py').write_text(code, encoding='utf-8')
        (sandbox / 'input.txt').write_text(stdin, encoding='utf-8')
        os.chmod(sandbox, 0o755)
        for path in sandbox.iterdir():
            os.chmod(path, 0o444)
        name = 'format-study-' + sandbox.name.lower().replace('_', '-')
        command = ['docker', 'create', '--pull=never', '--name', name, '-i',
                   '--network=none', '--read-only', '--cap-drop=ALL',
                   '--security-opt=no-new-privileges', '--memory=512m', '--memory-swap=512m',
                   '--cpus=1', '--pids-limit=64', '--ulimit', 'fsize=2048:2048',
                   '--user=65534:65534', '--tmpfs', '/tmp:rw,noexec,nosuid,size=16m',
                   '--mount', f'type=bind,src={sandbox},dst=/case,readonly',
                   '--workdir=/case', IMAGE, 'python', '-I', '-B', '/case/main.py']
        result = {}
        def execute():
            created = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
            if created.returncode:
                return {'status': 'INFRASTRUCTURE_ERROR', 'phase': 'create',
                        'error': created.stderr, 'docker_exit_code': created.returncode}
            started = time.monotonic()
            with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr, (sandbox / 'input.txt').open('rb') as input_file:
                process = subprocess.Popen(['docker', 'start', '--attach', '--interactive', name],
                                           stdin=input_file, stdout=stdout, stderr=stderr)
                failure = None
                while process.poll() is None:
                    if os.fstat(stdout.fileno()).st_size > OUTPUT_LIMIT or os.fstat(stderr.fileno()).st_size > OUTPUT_LIMIT:
                        failure = 'OUTPUT_LIMIT'
                        break
                    if time.monotonic() - started >= TIMEOUT:
                        failure = 'TIMEOUT'
                        break
                    time.sleep(0.02)
                if failure:
                    process.kill()
                    process.wait()
                    return {'status': failure, 'seconds': time.monotonic() - started}
                if os.fstat(stdout.fileno()).st_size > OUTPUT_LIMIT or os.fstat(stderr.fileno()).st_size > OUTPUT_LIMIT:
                    return {'status': 'OUTPUT_LIMIT', 'seconds': time.monotonic() - started}
                inspected = subprocess.run(['docker', 'inspect', '--format', '{{json .State}}', name],
                                           capture_output=True, text=True, timeout=15, check=False)
                if inspected.returncode:
                    return {'status': 'INFRASTRUCTURE_ERROR', 'phase': 'inspect', 'error': inspected.stderr}
                state = json.loads(inspected.stdout)
                if state.get('Running') or state.get('Error') or state.get('StartedAt', '0001').startswith('0001'):
                    return {'status': 'INFRASTRUCTURE_ERROR', 'phase': 'start', 'container_state': state}
                stdout.seek(0)
                stderr.seek(0)
                try:
                    output = stdout.read().decode('utf-8')
                    error = stderr.read().decode('utf-8')
                except UnicodeDecodeError:
                    return {'status': 'INVALID_UTF8', 'seconds': time.monotonic() - started}
                exit_code = state['ExitCode']
                if process.returncode != exit_code:
                    return {'status': 'INFRASTRUCTURE_ERROR', 'phase': 'attach', 'docker_exit_code': process.returncode, 'container_exit_code': exit_code}
                return {'status': 'OK' if exit_code == 0 else 'EXECUTION_ERROR',
                        'stdout': output, 'stderr': error, 'exit_code': exit_code,
                        'seconds': time.monotonic() - started}
        try:
            result.update(execute())
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            result.update(status='INFRASTRUCTURE_ERROR', error=str(exc))
        finally:
            try:
                cleanup = subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL,
                                         stderr=subprocess.PIPE, text=True, timeout=15, check=False)
                if cleanup.returncode and result.get('phase') != 'create':
                    result.update(prior_status=result.get('status'), status='INFRASTRUCTURE_ERROR',
                                  cleanup_error=cleanup.stderr)
            except (OSError, subprocess.TimeoutExpired) as exc:
                result.update(prior_status=result.get('status'), status='INFRASTRUCTURE_ERROR', cleanup_error=str(exc))
        return result

def grade(code, task, workers=1, on_case=None):
    inputs = task['input_output']['inputs']
    outputs = task['input_output']['outputs']
    if not inputs or len(inputs) != len(outputs):
        raise ValueError('Nonempty aligned cases required')
    cases = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for index, result in enumerate(pool.map(lambda stdin: run_case(code, stdin), inputs)):
            result['passed'] = result['status'] == 'OK' and matches(result.get('stdout', ''), outputs[index])
            cases.append(result)
            if on_case:
                on_case(index, result)
    return {'task_id': task['id'], 'all_pass': all(c['passed'] for c in cases),
            'passed': sum(c['passed'] for c in cases), 'total': len(cases), 'cases': cases}

def validate_references(root=ROOT):
    from prepare import tasks, digest, write_json
    rows = tasks(root)
    reports = []
    task_hashes = {r['id']: digest(root / 'source/selected' / r['id'] / 'task.json') for r in rows}
    evaluation_hashes = {r['id']: digest(root / 'source/selected' / r['id'] / 'evaluation-cases.json') for r in rows}
    ref_hashes = {r['id']: digest(root / 'source/selected' / r['id'] / 'reference.py') for r in rows}
    grader_hash = digest(Path(__file__).resolve())
    case_log = root / 'reference-validation.cases.jsonl'
    case_log.write_text('')
    for task in rows:
        source = root / 'source/selected' / task['id'] / 'reference.py'
        def record_case(index, result):
            inputs = task['input_output']['inputs']
            outputs = task['input_output']['outputs']
            entry = {'task_id': task['id'], 'evaluation_case_index': index, 'source_case_index': task['evaluation_case_indices'][index],
                     'input_sha256': hashlib.sha256(inputs[index].encode()).hexdigest(),
                     'expected_sha256': hashlib.sha256(outputs[index].encode()).hexdigest(),
                     'result': result}
            with case_log.open('a') as stream:
                stream.write(json.dumps(entry) + '\n')
        report = grade(source.read_text(), task, workers=3, on_case=record_case)
        reports.append(report)
        write_json(root / 'reference-validation.partial.json', {'status': 'INCOMPLETE', 'reports': reports})
        print(json.dumps({'task_id': task['id'], 'passed': report['passed'], 'total': report['total']}), flush=True)
    report = {'status': 'PASS' if all(r['all_pass'] for r in reports) else 'FAIL',
              'task_count': len(rows), 'grader_sha256': grader_hash, 'image': IMAGE, 'timeout_seconds_per_case': TIMEOUT,
              'comparison': 'exact whitespace-separated tokens',
              'task_sha256': task_hashes,
              'reference_sha256': ref_hashes, 'evaluation_sha256': evaluation_hashes,
              'reports': reports}
    write_json(root / 'reference-validation.json', report)
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate-references', 'grade'])
    parser.add_argument('--task', type=Path)
    parser.add_argument('--code', type=Path)
    args = parser.parse_args()
    if args.command == 'validate-references':
        if (ROOT / 'manifest.json').exists():
            parser.error('Frozen validation evidence cannot be overwritten')
        result = validate_references()
    else:
        if not args.task or not args.code:
            parser.error('--task and --code required')
        from prepare import verify, load_task
        verify(ROOT)
        task_path = args.task.resolve()
        task = json.loads(task_path.read_text())
        expected_path = (ROOT / 'source/selected' / task['id'] / 'task.json').resolve()
        if task_path != expected_path or task_path.parent.name != task['id']:
            parser.error('Task must match its frozen selected source path and ID')
        result = grade(args.code.read_text(), load_task(task_path, ROOT))
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result.get('status') == 'PASS' or result.get('all_pass') else 1)
