
"""Package entire system into timestamped zip in versions/."""
from datetime import datetime
import pathlib, zipfile, os, shutil, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]

# run tests in parallel
try:
    subprocess.run(['pytest','-n','auto','-q'], check=True)
except Exception as e:
    print('[WARN] Tests failed', e)

ver_dir = ROOT / 'versions'
ver_dir.mkdir(exist_ok=True)

stamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
zip_path = ver_dir / f'SYSTEME_META_CERVEAUX_V_{stamp}.zip'

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        if 'versions' not in p.parts:
            z.write(p, p.relative_to(ROOT))

# cleanup old
versions = sorted(ver_dir.glob('SYSTEME_META_CERVEAUX_V_*.zip'), key=os.path.getmtime, reverse=True)
for old in versions[5:]:
    old.unlink()

print('📦 Packaged', zip_path)

# verify signature before finish
subprocess.run(['python','tools/verify_signature.py', zip_path], check=False)
subprocess.run(['python','ci/delta_pack.py'], check=False)

subprocess.run(['python','ci/sign_zip.py'], check=False)


# Build Rust wheel if Cargo.toml exists
if (ROOT/'vector_router').exists():
    try:
        subprocess.run(['maturin','build','--release','-m','vector_router/Cargo.toml','-i','python3'], check=True)
        wheel = next((ROOT/'target'/'wheels').glob('vector_router*whl'))
        subprocess.run(['pip','install',wheel], check=False)
    except Exception as e:
        print('[WARN] Rust wheel build failed', e)

# size diff report
prev_zips = sorted(ver_dir.glob('SYSTEME_META_CERVEAUX_V_*.zip'), key=os.path.getmtime)
if len(prev_zips) >= 2:
    old = prev_zips[-2]
    new = prev_zips[-1]
    rep_path = ROOT / 'reports' / f'size_diff_{new.name}.txt'
    subprocess.run(['python', 'tools/compare_zip_sizes.py', old, new, rep_path], check=False)

