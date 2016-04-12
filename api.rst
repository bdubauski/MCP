==============================
CInP API Documentation for MCP
==============================

------------
Namespace - 
------------
URL: /api/v1/

API Version: v1


Model - Auth
------------

URL: /api/v1/Auth







Action - login
~~~~~~~~~~~~~~

URL: /api/v1/Auth(login)

Static: True



Return Type::

  None(String)(Req)

Paramaters::

  - username(String)(Req)
  - password(String)(Req)



Action - logout
~~~~~~~~~~~~~~~

URL: /api/v1/Auth(logout)

Static: True



Return Type::

  None(String)(Req)

Paramaters::

  - username(String)(Req)
  - token(String)(Req)



Action - keepalive
~~~~~~~~~~~~~~~~~~

URL: /api/v1/Auth(keepalive)

Static: True



Return Type::

  None(String)(Req)




--------------------
Namespace - .Project
--------------------
URL: /api/v1/Project

API Version: v1


Model - BuildDependancy
-----------------------

URL: /api/v1/Project/BuildDependancy


::

  BuildDependancy(key, build_id, package_id, state)




Fields
~~~~~~

::

  - state(String)(RW)(Req)
  - build(Model)(RW)(Req) uri: /api/v1/Project/Build
  - key(String)(R)(Req)
  - package(Model)(RW)(Req) uri: /api/v1/Project/Package



Model - Package
---------------

URL: /api/v1/Project/Package


::

  This is a Package




Fields
~~~~~~

::

  - updated(DateTime)(R)
  - name(String)(RC)(Req)
  - created(DateTime)(R)



Model - Project
---------------

URL: /api/v1/Project/Project


::

  This is a Generic Project




Fields
~~~~~~

::

  - status(String)(R)
  - updated(DateTime)(R)
  - busy(String)(R)
  - name(String)(RC)(Req)
  - created(DateTime)(R)
  - internal_git_url(String)(R)
  - upstream_git_url(String)(R)
  - repo(String)(R)
  - last_checked(DateTime)(RW)(Req)
  - org(String)(R)
  - type(String)(R)



Model - BuildResource
---------------------

URL: /api/v1/Project/BuildResource


::

  BuildResource(key, build_id, resource_id, name, quanity)




Fields
~~~~~~

::

  - quanity(Integer)(RW)(Req)
  - resource(Model)(RW)(Req) uri: /api/v1/Resource/Resource
  - build(Model)(RW)(Req) uri: /api/v1/Project/Build
  - key(String)(R)(Req)
  - name(String)(RW)(Req)



Model - Build
-------------

URL: /api/v1/Project/Build


::

  This is a type of Build that can be done



List Filters
~~~~~~~~~~~~

::

  - project - project(Model)(Req) uri: /api/v1/Project/Project

Fields
~~~~~~

::

  - updated(DateTime)(R)
  - name(String)(RW)(Req)
  - created(DateTime)(R)
  - manual(Boolean)(RW)
  - project(Model)(RW)(Req) uri: /api/v1/Project/Project
  - key(String)(R)(Req)
  - dependancies(ModelList)(RW)(Req) uri: /api/v1/Project/Package - <django.utils.functional.__proxy__ object at 0x7f110d36fa90>
  - networks(String)(RW)(Req)
  - resources(ModelList)(RW)(Req) uri: /api/v1/Resource/Resource - <django.utils.functional.__proxy__ object at 0x7f110d36fbd0>



Model - Commit
--------------

URL: /api/v1/Project/Commit


::

  A Single Commit of a Project


Constants
~~~~~~~~

::

  - STATE_LIST

List Filters
~~~~~~~~~~~~

::

  - project - project(Model)(Req) uri: /api/v1/Project/Project
  - in_process - 

Fields
~~~~~~

::

  - lint_results(String)(RW)(Req)
  - build_results(String)(RW)(Req)
  - lint_at(DateTime)(R)
  - created(DateTime)(R)
  - updated(DateTime)(R)
  - test_results(String)(RW)(Req)
  - project(Model)(RW)(Req) uri: /api/v1/Project/Project
  - state(String)(R)
  - test_at(DateTime)(R)
  - branch(String)(RW)(Req)
  - done_at(DateTime)(R)
  - build_at(DateTime)(R)
  - commit(String)(RW)(Req)
  - passed(Boolean)(R)
  - built(Boolean)(R)



Model - GitHubProject
---------------------

URL: /api/v1/Project/GitHubProject


::

  This is a GitHub Project




Fields
~~~~~~

::

  - updated(DateTime)(R)
  - name(String)(RC)(Req)
  - created(DateTime)(R)
  - _org(String)(RW)(Req)
  - _repo(String)(RW)(Req)
  - local_path(String)(R)
  - last_checked(DateTime)(RW)(Req)



Model - PackageVersion
----------------------

URL: /api/v1/Project/PackageVersion


::

  This is a Version of a Package




Fields
~~~~~~

::

  - state(String)(RW)(Req)
  - version(String)(RW)(Req)
  - created(DateTime)(R)
  - updated(DateTime)(R)
  - package(Model)(RW)(Req) uri: /api/v1/Project/Package



Model - GitProject
------------------

URL: /api/v1/Project/GitProject


::

  This is a Git Project




Fields
~~~~~~

::

  - updated(DateTime)(R)
  - name(String)(RC)(Req)
  - created(DateTime)(R)
  - local_path(String)(R)
  - git_url(String)(RW)(Req)
  - last_checked(DateTime)(RW)(Req)



-----------------------------
Namespace - .Project.Resource
-----------------------------
URL: /api/v1/Resource

API Version: v1


Model - ResourceGroup
---------------------

URL: /api/v1/Resource/ResourceGroup


::

  ResourceGroup




Fields
~~~~~~

::

  - updated(DateTime)(R)
  - created(DateTime)(R)
  - _config_list(String)(RW)(Req)
  - name(String)(RC)(Req)
  - description(String)(RW)(Req)



Model - HardwareResource
------------------------

URL: /api/v1/Resource/HardwareResource


::

  HardwareResource(name, description, config_profile, created, updated, resource_ptr_id, hardware_template)




Fields
~~~~~~

::

  - updated(DateTime)(R)
  - name(String)(RC)(Req)
  - created(DateTime)(R)
  - hardware_template(String)(RW)(Req)
  - config_profile(String)(RW)(Req)
  - description(String)(RW)(Req)



Model - Resource
----------------

URL: /api/v1/Resource/Resource


::

  Resource




Fields
~~~~~~

::

  - config_profile(String)(RW)(Req)
  - created(DateTime)(R)
  - updated(DateTime)(R)
  - name(String)(RC)(Req)
  - description(String)(RW)(Req)



Model - VMResource
------------------

URL: /api/v1/Resource/VMResource


::

  VMResource(name, description, config_profile, created, updated, resource_ptr_id, vm_template, build_ahead_count)




Fields
~~~~~~

::

  - updated(DateTime)(R)
  - vm_template(String)(RW)(Req)
  - name(String)(RC)(Req)
  - created(DateTime)(R)
  - config_profile(String)(RW)(Req)
  - build_ahead_count(Integer)(RW)(Req)
  - description(String)(RW)(Req)



Model - NetworkResource
-----------------------

URL: /api/v1/Resource/NetworkResource


::

  NetworkResource




Fields
~~~~~~

::

  - subnet(Integer)(RC)(Req)
  - updated(DateTime)(R)
  - created(DateTime)(R)



---------------------------------------
Namespace - .Project.Resource.Processor
---------------------------------------
URL: /api/v1/Processor

API Version: v1


Model - QueueItem
-----------------

URL: /api/v1/Processor/QueueItem


::

  QueueItem



List Filters
~~~~~~~~~~~~

::

  - project - project(Model)(Req) uri: /api/v1/Project/Project

Fields
~~~~~~

::

  - priority(Integer)(RW)(Req)
  - updated(DateTime)(R)
  - resource_groups(ModelList)(RW)(Req) uri: /api/v1/Resource/ResourceGroup - <django.utils.functional.__proxy__ object at 0x7f110d3c3750>
  - target(String)(RW)(Req)
  - created(DateTime)(R)
  - manual(Boolean)(RW)
  - resource_status(String)(RW)(Req)
  - project(Model)(RW)(Req) uri: /api/v1/Project/Project
  - build(Model)(RW)(Req) uri: /api/v1/Project/Build
  - branch(String)(RW)(Req)
  - commit(Model)(RW) uri: /api/v1/Project/Commit
  - promotion(Model)(RW) uri: /api/v1/Processor/Promotion



Action - queue
~~~~~~~~~~~~~~

URL: /api/v1/Processor/QueueItem(queue)

Static: True



Return Type::

  None(String)(Req)

Paramaters::

  - build(Model)(Req) uri: /api/v1/Project/Build



Model - Promotion
-----------------

URL: /api/v1/Processor/Promotion


::

  Promotion(id, to_state, created, updated)




Fields
~~~~~~

::

  - status(ModelList)(RW)(Req) uri: /api/v1/Project/Build - <django.utils.functional.__proxy__ object at 0x7f110d380190>
  - updated(DateTime)(R)
  - package_versions(ModelList)(RW)(Req) uri: /api/v1/Project/PackageVersion - <django.utils.functional.__proxy__ object at 0x7f110d380090>
  - to_state(String)(RW)(Req)
  - created(DateTime)(R)



Model - PromotionBuild
----------------------

URL: /api/v1/Processor/PromotionBuild


::

  PromotionBuild(id, promotion_id, build_id, status)




Fields
~~~~~~

::

  - status(String)(RW)(Req)
  - promotion(Model)(RW)(Req) uri: /api/v1/Processor/Promotion
  - build(Model)(RW)(Req) uri: /api/v1/Project/Build



Model - PromotionPkgVersion
---------------------------

URL: /api/v1/Processor/PromotionPkgVersion


::

  PromotionPkgVersion(id, promotion_id, package_version_id, packrat_id)




Fields
~~~~~~

::

  - promotion(Model)(RW)(Req) uri: /api/v1/Processor/Promotion
  - package_version(Model)(RW)(Req) uri: /api/v1/Project/PackageVersion
  - packrat_id(String)(RW)(Req)



Model - BuildJob
----------------

URL: /api/v1/Processor/BuildJob


::

  BuildJob


Constants
~~~~~~~~

::

  - STATE_LIST

List Filters
~~~~~~~~~~~~

::

  - project - project(Model)(Req) uri: /api/v1/Project/Project

Fields
~~~~~~

::

  - suceeded(String)(R)
  - updated(DateTime)(R)
  - ran_at(DateTime)(R)
  - target(String)(RW)(Req)
  - created(DateTime)(R)
  - built_at(DateTime)(R)
  - manual(Boolean)(RW)
  - acknowledged_at(DateTime)(R)
  - project(Model)(RW)(Req) uri: /api/v1/Project/Project
  - reported_at(DateTime)(R)
  - state(String)(R)
  - build(Model)(R)(Req) uri: /api/v1/Project/Build
  - branch(String)(RW)(Req)
  - released_at(DateTime)(R)
  - commit(Model)(RW) uri: /api/v1/Project/Commit
  - promotion(Model)(RW) uri: /api/v1/Processor/Promotion
  - networks(ModelList)(RW)(Req) uri: /api/v1/Resource/NetworkResource - <django.utils.functional.__proxy__ object at 0x7f110d3d2c50>
  - resources(String)(RW)(Req)



Action - getNetworkInfo
~~~~~~~~~~~~~~~~~~~~~~~

URL: /api/v1/Processor/BuildJob(getNetworkInfo)

Static: False



Return Type::

  None(String)(Req)

Paramaters::

  - name(String)(Req)



Action - setConfigValues
~~~~~~~~~~~~~~~~~~~~~~~~

URL: /api/v1/Processor/BuildJob(setConfigValues)

Static: False



Return Type::

  None(String)(Req)

Paramaters::

  - count(Integer)
  - index(Integer)
  - values(Map)(Req)
  - name(String)(Req)



Action - updateResourceState
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

URL: /api/v1/Processor/BuildJob(updateResourceState)

Static: False



Return Type::

  None(String)(Req)

Paramaters::

  - status(String)(Req)
  - index(Integer)(Req)
  - name(String)(Req)



Action - acknowledge
~~~~~~~~~~~~~~~~~~~~

URL: /api/v1/Processor/BuildJob(acknowledge)

Static: False



Return Type::

  None(String)(Req)




Action - jobRan
~~~~~~~~~~~~~~~

URL: /api/v1/Processor/BuildJob(jobRan)

Static: False



Return Type::

  None(String)(Req)




Action - getConfigStatus
~~~~~~~~~~~~~~~~~~~~~~~~

URL: /api/v1/Processor/BuildJob(getConfigStatus)

Static: False



Return Type::

  None(String)(Req)

Paramaters::

  - count(Integer)
  - index(Integer)
  - name(String)(Req)



Action - getProvisioningInfo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

URL: /api/v1/Processor/BuildJob(getProvisioningInfo)

Static: False



Return Type::

  None(String)(Req)

Paramaters::

  - count(Integer)
  - index(Integer)
  - name(String)(Req)



Action - setResourceSuccess
~~~~~~~~~~~~~~~~~~~~~~~~~~~

URL: /api/v1/Processor/BuildJob(setResourceSuccess)

Static: False



Return Type::

  None(String)(Req)

Paramaters::

  - index(Integer)(Req)
  - name(String)(Req)
  - success(Boolean)(Req)



Action - setResourceResults
~~~~~~~~~~~~~~~~~~~~~~~~~~~

URL: /api/v1/Processor/BuildJob(setResourceResults)

Static: False



Return Type::

  None(String)(Req)

Paramaters::

  - index(Integer)(Req)
  - name(String)(Req)
  - results(String)(Req)



Generated by CInP autodoc
*************************
