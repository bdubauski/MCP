Stages
======

In most places where the target is to "echo" something in a list, that list should be separated by " " or on separate lines.
duplicates are ignored.  The following examples all result in the same list::

  target-a:
    echo item1 item2 item3

  target-b:
    echo item1 item2
    echo item3

  target-c:
    echo item1 item2 item3
    echo item2

  target-d:
    echo item1
    make -C subdir target-d2
    echo item3

  (in subdir/Makefile)
  target-d2:
    echo item2

Make targets Run on MCP
-----------------------

- version: echo the value to be used for the version, string up to 50 characters long

example::

  version:
    echo 2.3

- <target>-distros. test-distros, doc-distros, dpkg-distros, rpm-distros, respkg-distros, resource-distros: echo a list of resource types
  that are used for the target( test, doc, dpkg, rpm, respkg, resource) to run on.

examples::

  test-distros:
    echo ubuntu-bionic

  dpkg-distros:
    echo ubuntu-bionic


- auto-builds: echo a list of builds that are automatically built when changes to the dependencies are detected, these
  can still be manually requested.  A <build>-depends is required to tell MCP what triggers the build.

example::

  auto-builds:
    echo installcheck

- manual-builds: echo a list of builds that can be built by request of a user or a script.  Any <build>-depends is ignored.

example::

  manual-builds:
    echo devlab

- <build>-resources: echo a list of resources that the build requires to run it's job.

examples::

  installcheck-resources:
    echo mcp:{ \"resource_name\": \"ubuntu-bionic-small\" }

  integrationcheck-resources:
    echo controller:{ \"resource_name\": \"ubuntu-xenial-small\", \"interface_map\": { \"eth0\": {}, \"eth1\": { \"network\": \"vmnet\", \"offset\": 10 } } }
    echo esx01:{ \"resource_name\": \"esx\", \"autorun\": true, \"interface_map\": { \"vmnic0\": {}, \"vmnic1\": { \"network\": \"vmnet\", \"offset\": 20 } } }

- <build>-networks: echo a list of networks required for the build.  If not specified, the resources will be attached to
  and available network with the required number of ip addresses available.

example::
  integrationcheck-networks:
    echo vmnet:{ \"min_size\": 128, \"dedicated\": true }

- <build>-depends: echo a list of packages and tags this auto build is triggered by.  NOTE: the build is triggered when
  the package is being tagged with the specified tag.  If the build fails, the package is tagged as failed.

example::

  integrationcheck-depends:
    echo architect:stage
    echo contractor:stage
    echo subcontractor:stage
    echo contractor-plugins:stage
    echo subcontractor-plugins:stage
    echo contractor-plugins-vs:stage
    echo demoservice:stage


Make targets Run on target resource (By nullunit)
-------------------------------------------------

nullunit setts the folling environment variables:

- NULLUNIT=1
- BUILD_NAME : for builds on the release branch this is a plain number, for other branches it is the number for the last
  release branch bhuld appended by '-<branch name>'.  forexample `14-_PR5`

if the target is *NOT* in `test`, packaging ( `dpkg`, `rpm`, `respkg`, `resource` ), or `doc`:

- RESOURCE_NAME - the name of the resource in the <build>-resource list
- RESOURCE_INDEX - the index offset this resource is, usually a 1 unless a count is specified in the <build>-resource.

- <target>-config: if the target is *NOT* in `test`, packaging ( `dpkg`, `rpm`, `respkg`, `resource` ), or `doc`.  echo configuration
  values to be pushed to contractor for this resource.

example::

  integration-check-config

- <target>-requires: echo a list of packages are required for the target.  These will be installed by the platform's packaging
  system, ie: yum and apt.

examples::

  test-requires:
    echo flake8 python3-pip python3-django python3-psycopg2 python3-cinp python3-dev python3-pytest python3-pytest-cov python3-pytest-django python3-pytest-mock postgresql python3-github

  dpkg-requires:
    echo dpkg-dev debhelper python3-dev python3-setuptools

- clean: clean up the source code of course, run between <target>-requires and <target>-setup

- <target>-setup: perform setup tasks, such as setup packaging config, this is called after the required packages are installed.

examples::

  test-setup:
    su postgres -c "echo \"CREATE ROLE mcp WITH PASSWORD 'mcp' NOSUPERUSER NOCREATEROLE CREATEDB LOGIN;\" | psql"
    pip3 install -e .
    cp mcp.conf.sample mcp/settings.py
    touch test-setup

  dpkg-setup:
    ./debian-setup
    touch dpkg-setup

- <target>-file: for packaging target.  return a list of files that should be uploaded to packrat.  For doc-file
  there also specify the page the file should be attached to.  For files going to packrat, a distro version should
  be specified if packrat will not be able to auto-detect the version.  And if the file type will not be auto-detectable
  a third parameter should be specified.

examples::

  dpkg-file:
    echo $(shell ls ../nullunit_*.deb)

  rpm-file:
    echo $(shell ls rpmbuild/RPMS/*/nullunit-*.rpm)

  dpkg-file:
    echo $(shell ls ../mcp_*.deb):bionic

  resource-file:
    echo $(shell ls ../mcp_*.tar):docker:docker

  doc-file:
          echo docs/mcp.pdf:34474541

- <target>, lint, test, dpkg, rpm, respkg, resource, doc: to the thing.  The output of this is sent to MCP to be stored
  in the commit, as well used to build the commit message.

examples::

  dpkg:
    dpkg-buildpackage -b -us -uc
    touch dpkg

  respkg:
    cd contractor && respkg -b ../mcp_$(VERSION)-1.respkg -n mcp -e $(VERSION) -c "MCP Blueprints for Contractor" -t load_data.sh -d resources -s contractor-os-base
    touch respkg

  integrationcheck:
  ifeq (controller, $(RESOURCE_NAME))
    ./test-files/setup
  endif
    touch integrationcheck
