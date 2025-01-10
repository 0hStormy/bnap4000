nuitka --standalone --onefile \
  --include-data-dir=./lang=lang \
  --include-module=_json \
  main.py
rm -rf main.dist/
rm -rf main.onefile-build/
rm -rf main.build/
