"""Build a Kodi-compatible install zip.

Kodi requires exactly one root entry, and it must be a folder named
after the addon id (plugin.audio.addict/), containing addon.xml.
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
ADDON_ID = 'plugin.audio.addict'
OUTPUT = os.path.join(os.path.dirname(ROOT), '%s.zip' % ADDON_ID)
SKIP_NAMES = {'.git', '.gitignore', 'build_zip.py', '__pycache__', '.DS_Store'}


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES]
        for filename in filenames:
            if filename in SKIP_NAMES:
                continue
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, ROOT).replace('\\', '/')
            yield rel_path, full_path


def build_zip():
    files = sorted(iter_files(), key=lambda item: item[0])

    if os.path.exists(OUTPUT):
        os.remove(OUTPUT)

    with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as archive:
        # Explicit folder entry so Kodi sees one root folder
        archive.writestr('%s/' % ADDON_ID, '')
        for rel_path, full_path in files:
            archive.write(full_path, '%s/%s' % (ADDON_ID, rel_path))

    with zipfile.ZipFile(OUTPUT) as archive:
        names = archive.namelist()
        roots = sorted({n.split('/')[0] for n in names if n})
        print('Created %s' % OUTPUT)
        print('  entries: %d' % len(names))
        print('  root folders/files: %s' % roots)
        print('  first entry: %s' % names[0])
        print('  sample:')
        for name in names[:8]:
            print('    %s' % name)


if __name__ == '__main__':
    build_zip()
