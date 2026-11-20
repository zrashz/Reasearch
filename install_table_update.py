"""Install only new, hash-checked integration files; never overwrite changes."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True)
    args=parser.parse_args()
    project=Path(args.project).resolve()
    if not project.is_dir():raise ValueError('Project does not exist')
    bundle=Path(__file__).resolve().parent
    manifest=json.loads((bundle/'update_manifest.json').read_text())
    for relative,expected in manifest['dependencies'].items():
        path=project/relative
        if not path.is_file() or sha(path)!=expected:
            raise ValueError('Uploaded source dependency differs: '+relative)
    staged=[]
    for relative,expected in manifest['files'].items():
        source=bundle/relative;target=(project/relative).resolve()
        if not target.is_relative_to(project):raise ValueError('Unsafe destination')
        if sha(source)!=expected:raise ValueError('Bundle hash mismatch: '+relative)
        if target.exists() and sha(target)!=expected:
            raise ValueError('Different file exists; preserved: '+relative)
        staged.append((source,target,relative))
    added=[]
    for source,target,relative in staged:
        if target.exists():continue
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(source.read_bytes())
        added.append(relative)
    print(json.dumps({'installed':added,'datasets_modified':False,
                      'historical_results_modified':False,'models_run':False},indent=2))

if __name__=='__main__':main()
