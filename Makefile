CWD    = $(CURDIR)
MODULE = $(notdir $(CWD))

NOW = $(shell date +%d%m%y)
REL = $(shell git rev-parse --short=4 HEAD)

PIP = $(CWD)/bin/pip3
PY  = $(CWD)/bin/python3
JPY = $(CWD)/bin/jupyter

.PHONY: all
all: wsgi

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
	$(PIP) install -U -r requirements.txt
	$(MAKE) requirements.txt

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
MERGE += requirements.txt $(MODULE).ipynb
MERGE += metaL.py metaL.ini static templates
MERGE += pythonanywhere uwsgi.ini

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
