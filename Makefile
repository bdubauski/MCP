DISTRO_NAME := $(shell lsb_release -sc | tr A-Z a-z)

all:
	./setup.py build

install:
	mkdir -p $(DESTDIR)/var/www/mcp/ui
	mkdir -p $(DESTDIR)/var/www/mcp/api
	mkdir -p $(DESTDIR)/etc/apache2/sites-available
	mkdir -p $(DESTDIR)/etc/mcp
	mkdir -p $(DESTDIR)/usr/lib/mcp/cron
	mkdir -p $(DESTDIR)/usr/lib/mcp/util
	mkdir -p $(DESTDIR)/usr/lib/mcp/setup
	cp -a ui/* $(DESTDIR)/var/www/mcp/ui
	install -m 644 api/mcp.wsgi $(DESTDIR)/var/www/mcp/api
	install -m 644 apache.conf $(DESTDIR)/etc/apache2/sites-available/mcp.conf
	install -m 644 master.conf.sample $(DESTDIR)/etc/mcp
	install -m 755 lib/cron/* $(DESTDIR)/usr/lib/mcp/cron
	install -m 755 lib/util/* $(DESTDIR)/usr/lib/mcp/util
	install -m 755 lib/setup/* $(DESTDIR)/usr/lib/mcp/setup

	./setup.py install --root $(DESTDIR) --install-purelib=/usr/lib/python3/dist-packages/ --prefix=/usr --no-compile -O0

clean:
	./setup.py clean
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
	echo dpkg-dev debhelper python-dev python-setuptools

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

dpkg-file:
	echo $(shell ls ../mcp_*.deb):bionic

.PHONY:: dpkg-distros dpkg-requires dpkg-file

respkg-distros:
	echo bionic

respkg-requires:
	echo respkg

respkg:
	cd contractor && respkg -b ../mcp-contractor_0.0.respkg -n mcp-contractor -e 0.0 -c "MCP Blueprints for Contractor" -t load_data.sh -d resources -s contractor-os-base
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
