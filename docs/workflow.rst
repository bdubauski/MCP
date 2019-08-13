Workflow
========

MCP will periodically poll Git/GitHub for new commits to all branches detected.  NOTE: GitHub Pull Requests
will appear as branches named `_PR#`.  MCP pulls the latest commit to an internal staging git repo, from there it
clones a copy and run a vew make commands (detailed latter).  The resources that are spooled up by MCP clone from this
internal staging git repo.

pseudo code of the project scanner::

  for each project:
    if project has commit records that are not done:
      skip project

    for each job in project:
      if the job is manual and has not completed running:
        skip project

      if the job is automatic and has not reported it's results:
        skip project

    update internal git copy from upstream (git pull)

    for each branch:
      if a commit record exist for the latest commit on the branch:
        skip branch

      create a commit record for this commit

      checkout branch to a working directory

      if there isn't a Makefile or the Makefile is invalid:
        fail the commit
        skip branch

      retrieve the version by running `make version`

      if there isn't a version:
        fail the commit
        skip the branch

      store the version number in the commit record

      if branch name is 'master':
        increment the project build counter

      retrieve the list of resources for test by running `make test-distros`

      for packaging in 'dpkg', 'rpm', 'respkg', 'resource':
        retrieve list of resources for packaging by running `make <packaging>-distros`

      if branch name is 'master':
        retrieve list of resources for documentation by running `make doc-distros`

      retrieve list of auto(integration testing) builds by running `make auto-builds`

      retrieve list of manual builds by running `make manual-builds`

      for each builds:
        retrieve list of package dependencies by running `make <build>-depends`
        retrieve list of resources by running `make <build>-resources`
        retrieve list of networks by running `make <build>-networks`


After the commit records are created, MCP goes over targets and allocates resources.  The
targets are `test`, packaging ( `dpkg`, `rpm`, `respkg`, `resource` ) and if the commit
is for the master branch `doc`.


pseudo code for the resource running a target::

  clone the repo from the staging/internal git
  checkout the branch/commit

  if target is not `test`, packaging, and `doc`:
    get configuration falues to push to contractor via `make <target>-config`

  retrieve the required packages by running `make <target>-requires`
  install the packages (via yum/apt)
  clean by running `make clean`

  setup for target by running `make <target>-setup`

  if target is `test`:
    do lint check with `make lint`
    to unit/self test(s) with `make test`

  else if packaging:
    build the package with `make <target>`
    retrieve the list of files by `make <target>-file`
    if branch is master:
      upload file(s) to packrat

  else if `doc` and branch is master:
    build the documents with `make doc`
    retrieve the list of files with `make doc-file`
    upload file(s) to confluence

  else:
    do the target with `make <target>`

MCP will then record the results for each of the target stages back to the commit.  If any stage fails,
processing stopps at that point.  If the test coverage is outputed in a format that Nullunit understands
the coverage value is also stored in the commit.  When the commit is finished processing, a results
summary is posted as a comment to the commit, if it is a PR branch then MCP sets the status check, which
enables protection on PR merging to block on test/lint/packaging results.  If the coverage drops from
commit to the next, there is a warning posted on the commit message.
