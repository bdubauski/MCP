Workflow
========

MCP will periodically poll Git/GitHub for new commits to all branches detected.  NOTE: GitHub Pull Requests
will apear as branches named `_PR#`.

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
