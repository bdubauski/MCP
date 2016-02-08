MCP
===

General plan and thoughts, most of the first part is in place, thoughts at the end are not

register git repo with mcp

stages:
  master branch change:
    for each test-distros
      build distro, sync code, install depends, `make lint` then `make test`
      post results of each stage for each distro to the PRs comments
      if any failes stop at that point
    for each dpkg-distros:
      build distro, sync code, install depends, `make dpkg`
    for each rpm-distros:
      build distro, sync code, install depends, `make rpm`
    for each respkg-distros:
      build distro, sync code, install depends, `make respkg`
    for each resource-distros:
      build distro, sync code, install depends, `make resource`
    promote new -> ci
    run all auto-builds on projects that depend on ci stage
    promote ci -> dev
    run all auto-builds on projects that depend on dev stage
    promote dev -> staging

    promotion to prod is done manually with CC info

  Peer Review creation:
    for each test-distros
      build distro, sync code, install depends, `make lint` then `make test`
      post results of each stage for each distro to the PRs comments


project distros:
    Called on MCP:

  test-distros: -> distros to run unit tests on (lint will also be run on these distro)
  dpkg-distros: -> distros to build dpkg on
  rpm-distros: -> distros to build rpm on
  respkg-distros: -> distros to build respkg on
  resource-distros: -> distros to build plato disk on

    Called on Distros
        NOTE for these dependancies: these are package dependancies to be installed via apt/yum, NOT not used to caculate builds/tests
  lint-requires: -> lint dependancies, will be called on the distro lint box
  test-requires: -> unit test dependancy, will be called on the distro test box
  dpkg-requires: -> dpkg build dependancies ( include dpkg-dev package if used), will be called on the distro build box
  rpm-requires: -> rpm build dependancies (see dpkg-depends)
  respkg-requires: -> respkg build dependancies (see dpkg-depends)
  resource-requires -> plato disk build dependancies (see dpkg-depends)

  lint: -> lint (run before test on test distros)
  test: -> unit tests (run on distros)
  dpkg: -> make debian package (if builds for multiple version add the version number to the package name) (runs on distros), NOTE: make clean and make dpkg-setup are called before make dpkg, for cleaning and optional setup
  rpm: -> make rpm (see dpkg)
  respkg: -> make respkg (see respkg)
  resource: -> plato disk (see dpkg)
  dpkg-file: -> echo the path to the built file build by dpkg
  rpm-file: -> (see dpkg-file)
  respkg-file: -> (see dpkg-file)
  resource-file: -> (see dpkg-file)

package distros: (called on MCP)
  auto-builds: ->
  manual-builds: ->
  <build name>-depends: -> ci/dev projects this build has the ability to block (only for auto-builds)
  <build name>-resources: ->
  <build name>-networks: ->

package distros: (called on distro)
  <build name>-config: ->
  <build name>-requires: ->
  <build name>-setup: ->


work flow:

Github commit event detected
git pull to git copy on mcp
git checkout master
make a commit reccord
make .....

for each distro for test distros:
  make build targeting that distro
  make -s lint-requires
     (install the returned packages)
  make lint
     ( if return code is 0, all is good, cary on, output is posted to slack and keep in the commit record)
clean up the lint VMs

for each distro for test distros:
  make build targing that distro
  make -s test-requires
     (install the returnd packages)
  make test
     ( if return code is 0, all is good, cary on, output is posted to slack and keep in the commit record)
clean up the test VMs

for each distro in rpm, dpkg, respkg, resource distros
  make build targing that distro
  make -s <rpm|dpkg|respkg|resource>-requires
     (install the returnd packages)
  make clean
  make setup-<rpm|dpkg|respkg|resource>
  make <rpm|dpkg|respkg|resource>
     ( if return code is 0, all is good, cary on, output is posted to slack and keep in the commit record)
  make <rpm|dpkg|respkg|resource>-file
     for each filename returned, check to see if it allready exists on packrat, if not, upload it

clean up the build VMs



Future thoughts and todos:
--------------------------

Makefile tells what other projects it depends on

Makefile tells what resources are needed to build/test
  ie... if the test is to build a cluster it needs to say it needs a vcenter with X compute resources and describe the vcenter config

Have utilities avaible to the Makefile to build a plato-master and load it with X files, etc

monitor for branches starting with "pr-" and pull and run the lint and unittests, make commit message with the results

monitor for changes on devel branch, auto merge to master after full test suite has passed, make commite message wih the results, incrament the build number in the changelog on the devel branch after merging to master
  No.... not going to mess with merging, only going to build off of master, should do some kind of test to make sure the version incramented, otherwise packrat won't take the new files

set git tag when packages are built

dependancies:
  dependancie comes from packrat package-name
  prefixed with ci/dev to know what version to look at

Testing ordering:
  order by projects from fewest dependancies to the most
