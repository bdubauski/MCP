Stages
======



stages:
  master branch change:
    for each test-distros
      build distro, sync code, install depends (from `make test-requires`), then 'make clean' then `make test-setup` then `make lint` then `make test`
      post results of each stage for each distro to the PRs comments
      if any failes stop at that point
    for each dpkg-distros:
      build distro, sync code, install depends (from `make dpkg-requires`), then 'make clean' then `make dpkg-setup`, `make dpkg`
    for each rpm-distros:
      build distro, sync code, install depends (from `make rpm-requires`), then 'make clean' then `make rpm-setup`, `make rpm`
    for each respkg-distros:
      build distro, sync code, install depends (from `make respkg-requires`), then 'make clean' then `make respkg-setup`, `make respkg`
    for each resource-distros:
      build distro, sync code, install depends (from `make resource-requires`), then 'make clean' then `make resource-setup`, `make resource`
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

  test-distros: -> distros to run lint and unit tests
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

  dpkg-setup:
  rpm-setup:
  respkg-setup:
  resource-setup:

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
