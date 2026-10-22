import argparse
import hashlib
import pathlib
import urllib.request

parser = argparse.ArgumentParser(description='Acquire pinned TACO Parquet as data. Does not execute dataset or reference code.')
parser.add_argument('destination', type=pathlib.Path)
args = parser.parse_args()
url = 'https://huggingface.co/datasets/BAAI/TACO/resolve/d593ed0a2becbbc952230bb89be09189bf1056dc/ALL/test-00000-of-00001.parquet'
expected = '5d99adc603500c05751aff9f61bed7bbd54a9ad5ea569d108b645346655aae44'
args.destination.parent.mkdir(parents=True, exist_ok=True)
if not args.destination.exists():
    temporary = args.destination.with_suffix('.partial')
    urllib.request.urlretrieve(url, temporary)
    actual = hashlib.sha256(temporary.read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f'Shard checksum mismatch: {actual}')
    temporary.replace(args.destination)
actual = hashlib.sha256(args.destination.read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit(f'Shard checksum mismatch: {actual}')
print(f'Verified {args.destination.stat().st_size} bytes SHA256 {actual}')
