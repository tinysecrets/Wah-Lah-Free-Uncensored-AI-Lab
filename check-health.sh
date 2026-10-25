#!/usr/bin/env bash
set -u
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
python3 - "$ROOT" <<'PY'
import json, pathlib, sys, urllib.request, shutil
root=pathlib.Path(sys.argv[1])
s=json.loads((root/'config/settings.json').read_text())
m=json.loads((root/'config/models.json').read_text())
print('Wah-Lah Free Uncensored AI Lab — non-invasive preflight')
print('Allowlist:', ', '.join(x['id'] for x in m['models']))
print('Free-only:', m.get('free_only') is True)
print('Automatic model fallback:', 'DISABLED' if m.get('automatic_fallback') is False else 'NOT STRICT')
print('Inference API:', s['api_base_url'])
key=root/s.get('api_key_file','.secrets/openrouter-api-key')
print('OpenRouter key file:', 'present' if key.is_file() and key.stat().st_size else 'missing')
if key.is_file():
    print('OpenRouter key file permissions:', oct(key.stat().st_mode & 0o777))
try:
    with urllib.request.urlopen(s['ping_url'], timeout=3) as r:
        print('Existing FreeLLMAPI health:', r.status, r.read(200).decode('utf-8','replace'))
except Exception as e:
    print('Existing FreeLLMAPI health: UNAVAILABLE —', type(e).__name__)
print('Sandbox runtime:', 'bubblewrap available' if pathlib.Path('/usr/bin/bwrap').is_file() else 'NOT AVAILABLE')
print('Speech output:', 'spd-say available' if shutil.which('spd-say') else 'NOT AVAILABLE')
PY
