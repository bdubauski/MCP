DISTRO_NAME := $(shell lsb_release -sc | tr A-Z a-z)

all:

clean:
	$(RM) -r build
	$(RM) dpkg
	dh_clean

test-distros:
	echo precise

test-requires:
	echo plato-master respkg

test:
	tests/setupMaster test/setup-answers

lint-requires:
# linter not in precise	echo linter

lint:
#	linter -i manage.py -i mcp/Processor/migrations/ -i mcp/Resource/migrations/ -i mcp/Project/migrations

dpkg-distros:
	echo precise

dpkg-requires:
	echo dpkg-dev debhelper cdbs python-dev python-setuptools

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

dpkg-file:
	echo $(shell ls ../mcp_*.deb):precise


.PHONY:: all clean test-distros test-requires test lint-requires lint dpkg-distros dpkg-requires dpkg dpkg-file

# builds
auto-builds:
	echo installcheck

installcheck-depends:
	echo mcp:ci
	echo plato:dev

installcheck-resources:
	echo plato-master:1:small-generic-precise

installcheck-requires:
	echo plato-master mcp

installcheck:
	cd tests && ./setupMaster setup-answers
	nullunitInterface --signal-ran
	touch installcheck

.PHONY:: auto-builds installcheck-depends installcheck-resources installcheck-requires
