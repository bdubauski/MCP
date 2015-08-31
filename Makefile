DISTRO_NAME := $(shell lsb_release -sc | tr A-Z a-z)

ifneq (precise, $(DISTRO_NAME))
$(error Only for precise builds)
endif

all:

test-requires:

test:

full-test: test
	./manage.py test

lint-requires:
	echo linter

lint:
	../linter/linter -c ../linter.json -i manage.py -i mcp/Processor/migrations/ -i mcp/Resource/migrations/ -i mcp/Project/migrations

dpkg-requires:
	echo dpkg-dev debhelper cdbs

dpkg-setup:


dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

.PHONY: test full-test lint dpkg-requires dpkg-setup dpkg
