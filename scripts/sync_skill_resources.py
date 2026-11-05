#!/usr/bin/env python3
"""Distribute shared template/entrypoints and Codex skill instructions to all platforms."""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORMS = ('.agents', '.qoder', '.trae')
SKILLS = ('lzk-paper-reading', 'html-paper-slides', 'blog-to-slides')
ENTRYPOINTS = {'html-paper-slides': ('pdf_extractor',),
               'blog-to-slides': ('build_asset_ledger', 'verify_slides')}


def outputs():
    for platform in PLATFORMS:
        for skill in SKILLS:
            folder = ROOT / platform / 'skills' / skill
            if platform != '.agents':
                text = (ROOT / '.agents/skills' / skill / 'SKILL.md').read_text(encoding='utf-8')
                yield folder / 'SKILL.md', text.replace('.agents/skills/', f'{platform}/skills/')
            if skill.endswith('slides'):
                yield folder / 'templates/presentation.html', (ROOT / 'templates/presentation.html').read_text(encoding='utf-8')
            for module in ENTRYPOINTS.get(skill, ()):
                yield folder / 'scripts' / f'{module}.py', (
                    '#!/usr/bin/env python3\n"""Generated entrypoint; implementation lives in repository scripts/."""\n'
                    'import sys\nfrom pathlib import Path\n'
                    'sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))\n'
                    f'from {module} import main\n\n'
                    'if __name__ == "__main__":\n    main()\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    drift = []
    for path, text in outputs():
        if path.exists() and path.read_text(encoding='utf-8') == text:
            continue
        drift.append(str(path.relative_to(ROOT)))
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
    print(('Drift: ' if args.check else 'Updated: ') + str(len(drift)))
    if args.check and drift:
        print('\n'.join(drift))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
