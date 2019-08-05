Intro
=====

MCP works by executing various targets in a Makefile.  Some targets are run on the MCP server, while most are run
on resources that are spun up to run those tasks.  After the task is complete, the resource is cleaned up.  All configuration
for a project are extracted from the Makefile.  The project only needs to be registered with MCP, by setting the Git/Github
information.
