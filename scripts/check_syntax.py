import glob
import py_compile

errors = []
for f in glob.glob('pycalphad_app/**/*.py', recursive=True):
    try:
        py_compile.compile(f, doraise=True)
    except Exception as e:
        errors.append((f, str(e)))

if errors:
    print(f"Found {len(errors)} syntax errors:")
    for f, err in errors:
        print(f, err)
else:
    print("All python files compiled with zero syntax errors!")
