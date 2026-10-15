.PHONY: test sync check

test:
	python3 -m pytest -q tests

sync:
	cp tools/wiki_check.py tools/wiki_manifest.py kb-central/tools/
	cp tools/wiki_check.py tools/wiki_manifest.py repo-template/tools/

check:
	python3 tools/wiki_check.py --root kb-central
	python3 tools/wiki_check.py --root repo-template
