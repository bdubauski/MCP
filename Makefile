DISTRO_NAME := $(shell lsb_release -sc | tr A-Z a-z)

all:

test-distros:
	echo precise

test-requires:
	echo django postgres

test:
	./manage.py test

lint-requires:
	echo linter

lint:
	linter -i manage.py -i mcp/Processor/migrations/ -i mcp/Resource/migrations/ -i mcp/Project/migrations

dpkg-distros:
	echo precise

dpkg-requires:
	echo dpkg-dev debhelper cdbs

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

dpkg-file:
	echo $(shell ls ../mcp_*.deb)


.PHONY: test-distros test-requires test lint-requires lint dpkg-distros dpkg-requires dpkg
