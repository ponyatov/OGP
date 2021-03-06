CWD    = $(CURDIR)
MODULE = $(notdir $(CWD))

NOW = $(shell date +%d%m%y)
REL = $(shell git rev-parse --short=4 HEAD)

PIP = $(CWD)/bin/pip3
PY  = $(CWD)/bin/python3
PYT = $(CWD)/bin/pytest
JPY = $(CWD)/bin/jupyter

.PHONY: all
all: py

.PHONY: test
test: $(PYT) test_metaL.py
	$^

.PHONY: py
py: $(PY) metaL.py metaL.ini
	$^

.PHONY: wsgi
wsgi: uwsgi.ini
	uwsgi --ini $<

.PHONY: jupyter
jupyter: $(JPY)
	$(JPY) notebook $(MODULE).ipynb

.PHONY: install
install: os $(PIP)
	$(PIP) install    -r requirements.txt
	$(MAKE) requirements.txt

.PHONY: update
update: os $(PIP)
	git pull
	$(PIP) install -U    pip
	$(PIP) install -U -r requirements.txt
	$(MAKE) requirements.txt

.PHONY: anywhere
anywhere: $(PIP)
	git pull -v
	$(PIP) install -r pythonanywhere/requirements.txt
	$(MAKE) test
	touch /var/www/kbase_pythonanywhere_com_wsgi.py

$(PIP) $(PY):
	python3 -m venv .
	$(PIP) install -U pip autopep8

.PHONY: requirements.txt
requirements.txt: $(PIP)
	$< freeze | grep -v 0.0.0 > $@

.PHONY: os
ifeq ($(OS),Windows_NT)
os: windows
else
os: debian
endif

.PHONY: debian
debian:
	sudo apt update
	sudo apt install -u `cat apt.txt`

.PHONY: master shadow release zip

MERGE  = Makefile README.md .gitignore .vscode apt.txt
MERGE += requirements.txt requirements.jupyter $(MODULE).ipynb
MERGE += metaL.py test_metaL.py metaL.ini static templates
MERGE += pythonanywhere uwsgi.ini
MERGE += img
MERGE += droid

master:
	git checkout $@
	git checkout shadow -- $(MERGE)

shadow:
	git checkout $@

release:
	git tag $(NOW)-$(REL)
	git push -v && git push -v --tags
	git checkout shadow

zip:
	git archive --format zip --output $(MODULE)_src_$(NOW)_$(REL).zip HEAD


IMG += img/compiler.png
IMG += img/ModelTrans.png

.PHONY: img
img: $(IMG)

img/%.png: img/%.dot
	dot -Tpng -o $@ $<
