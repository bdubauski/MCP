DISTRO_NAME := $(shell lsb_release -sc | tr A-Z a-z)

all:

clean:
	$(RM) -r build
	$(RM) dpkg
	dh_clean

.PHONY:: all clean

test-distros:
	echo bionic

test-requires:
	echo plato-master respkg

test:
	tests/setupMaster $(CURDIR)/tests/setup-answers

lint-requires:
# linter not in precise	echo linter

lint:
#	linter -i manage.py -i mcp/Processor/migrations/ -i mcp/Resource/migrations/ -i mcp/Project/migrations

.PHONY:: test-distros test-requires test lint-requires lint

dpkg-distros:
	echo bionic

dpkg-requires:
	echo dpkg-dev debhelper cdbs python-dev python-setuptools

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

dpkg-file:
	echo $(shell ls ../mcp_*.deb):bionic

.PHONY:: dpkg-distros dpkg-requires dpkg dpkg-file

respkg-distros:
	echo bionic

respkg-requires:
	echo respkg

respkg:
	cd blueprints && respkg -b ../mcp_blueprints_0.0.respkg -n mcp_blueprints -e 0.0 -c "MCP Blueprints for loading into Contractor" -t load_contractor_data.sh -d resources
	touch respkg

respkg-file:
	echo $(shell ls *.respkg)

.PHONY:: respkg-distros respkg-requires respkg respkg-file

# builds
auto-builds:
	echo installcheck

installcheck-depends:
	echo mcp:dev
	echo plato-master:stage

installcheck-resources:
	echo plato-master:1:small-generic-bionic

installcheck-requires:
	echo plato-master mcp

installcheck:
	cd tests && ./setupMaster setup-answers
	nullunitInterface --signal-ran
	touch installcheck

.PHONY:: auto-builds installcheck-depends installcheck-resources installcheck-requires
