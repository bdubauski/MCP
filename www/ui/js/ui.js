var mcp;

$( document ).ready(
  function ()
  {
    var cinp = cinpBuilder();
    cinp.on_server_error = errorHandler;

    mcp = mcpBuilder( cinp );

    $( '#home-tab' ).addClass( 'active' );
    $( '#project-panel' ).hide();

    $( window ).on( 'hashchange', hashChange );
    hashChange();

    $( '#login' ).click( function(event ){
      event.preventDefault();
      user = $( '#username' ).val();
      var pass = $( '#password' ).val();

      $.when( mcp.login( user, pass ) ).then(
        function( token )
        {
          $.cookie( 'user', user );
          $.cookie( 'token', token );
          location.reload()
        }
      ).fail(
        function( reason )
        {
          errorHandler( "Login Failure", reason.msg );
        }
      );
    });

    $( '#doLogout' ).click( function( event ) {
      event.preventDefault();
      $.removeCookie( 'user' );
      $.removeCookie( 'token' );
      $( '#user-logged-in' ).hide();
      $( '#user-logged-out' ).show();

      clearInterval( keepalive_interval );
      cinp.setAuth( '', '' );
      mcp.logout( user, token );

      user = undefined;
      token = undefined;
    });

    user = $.cookie( 'user' );
    token = $.cookie( 'token' );
    if( user )
    {
      $( '#user-logged-out' ).hide();
      $( '#username' ).empty();
      $( '#user' ).html( '<strong>' + user + ' </strong>' );
      $('a').tooltip();
      cinp.setAuth( user, token );
      permissions()
      keepalive_interval = setInterval(
        function()
        {
          mcp.keepalive();
        }, 60000 );
    } else {
      $( '#user-logged-in' ).hide();
    }
  }
);

function permissions() {
  mcp.permissions();
}

function mcpModal(title, body, footer) {
  $('.modal-title').html(title);
  $('.modal-body').html(body);
  $('.modal-footer').html(footer);
  $('#modalbox').modal('show');
}

function errorHandler( msg, stack_trace )
{
  mcpModal( msg, '<pre>' + stack_trace + '</pre>', '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>' );
}

function isToday(dt) {
  var today = new Date();
  return today.toDateString() == new Date(dt).toDateString();
}

jQuery.fn.sortDivs = function sortDivs() {
  $("> div", this[0]).sort(asc_sort).appendTo(this[0]);
  function asc_sort(a, b){ return ($(b).attr("timestamp")) > ($(a).attr("timestamp")) ? 1 : -1; }
}

function hashChange( event )
{
  var mainTitle = $( '#main-title' );
  $( '#home-tab' ).removeClass( 'active' );
  $( '#project-tab' ).removeClass( 'active' );
  $( '#global-tab' ).removeClass( 'active' );
  $( '#help-tab' ).removeClass( 'active' );

  var hash = location.hash;
  var pos = hash.indexOf( '/' );
  var type = 'home';
  var id;
  var path;

  if( pos == -1 )
  {
    if( hash === '' )
    {
      type = 'home';
    } else {
      type = hash.substr( 1 );
    }
  } else {
    type = hash.substr( 1, pos - 1 );
    id = atob( hash.substr( pos + 1 ) );
    path = id.split(':')[1]
  }

  var latestCommitEntry;
  var jobEntries;
  var queueEntries;
  var commitEntries;
  var buildEntries;

  if( type === 'project' )
  {
     loadProjects();
    $( '#project-panel' ).show();
    $( '#project-detail' ).show();
    $( '#global-detail' ).hide();
    $( '#project-tab' ).addClass( 'active' );

    if( id )
    {
      latestCommitEntry = $( '#project-latest-commit' );
      commitEntries = $( '#project-commit-list' );
      jobEntries = $( '#project-build-jobs' );
      queueEntries = $( '#project-queued-jobs' );
      buildEntries = $( '#project-builds' );

      $.when( mcp.getObject( id ) ).then(
        function( data )
        {
          data = data.detail;
          var buildPass = '';
          var jobBuilt = data.status.built
          buildPass += '<span>'
          if( data.status.passed )
          {
            buildPass += '<img src="/ui/image/test-pass.svg" /> ';
          } else if( data.status.passed == null )
          {
          } else {
            buildPass += '<img src="/ui/image/test-error.svg" /> ';
          }

          if( data.status.built )
          {
            buildPass += '<img src="/ui/image/build-pass.svg" />';
          } else if( data.status.built == null )
          {
          } else {
            buildPass += '<img src="/ui/image/build-error.svg" />';
          }
          buildPass += '</span>'
          if( data.type == 'GitHubProject' )
          {
            mainTitle.html( '<a href="https://github.emcrubicon.com/' + data.org + '" target="_blank">' + data.org + '</a> / <a href="https://github.emcrubicon.com/' + data.org + '/' + data.repo + '" target="_blank">' + data.repo + '</a> <i class="fa fa-github fa-fw"/>' + buildPass );
          } else if( data.type == 'GitProject' ) {
            mainTitle.html( '<a href="' + data.upstream_git_url + '" target="_blank">' + data.upstream_git_url + '</a>' + buildPass );
          } else {
            mainTitle.html( data.name + buildPass );
          }

          $.when( mcp.getCommits( id ) ).then(
            function( data )
            {
              var commitEntry = ''
              for( var uri in data )
              {
                var item = data[ uri ];
                var commit = item.commit
                var timestamp = new Date(item.updated).getTime()
                var buildResult = ''
                if( ( item.passed && ( item.built || item.built == null )) || item.built && ( item.passed || item.passed == null ) )
                {
                  var panelStatus = 'panel-success'
                  var textStatus = 'text-success'
                } else {
                  var panelStatus = 'panel-danger'
                  var textStatus = 'text-danger'
                }
                commitEntry += '<div class="panel ' + panelStatus + '" timestamp="' + timestamp + '"><div class="panel-body" id="commit-' + commit + '"><ul class="list-inline"><li class="' + textStatus + '"><strong><i class="fa fa-code-fork fa-fw"></i> ' + commit + '</strong></li></ul></div><ul class="list-group"><a class="list-group-item" data-toggle="collapse" data-target="#build-' + commit + key + subkey + '" data-parent="#commit-' + commit + '"><ul class="list-inline text-muted"><li>branch: ' + item.branch + '</li>'
                if( item.passed)
                {
                  commitEntry += '<li class="text-success">test passed</li>'
                } else if( !item.passed && item.passed != null ) {
                  commitEntry += '<li class="text-danger">test failed</li>'
                }

                if( item.built )
                {
                  commitEntry += '<li>' + subkey + '&nbsp;' + key + ' build succeeded</li>'
                } else if( !item.built && item.built != null ) {
                  commitEntry += '<li>project build failed</li>'
                }

                commitEntry += '</ul></a><div id="build-' + commit + key + subkey + '" class="sublinks collapse"><div class="list-group-item"><ol class="small">'
                var lintResults = ( item.lint_results )
                if( !jQuery.isEmptyObject( lintResults ) )
                {
                  var lintResults = jQuery.parseJSON( lintResults )
                  for(var key in lintResults)
                  {
                    var lintResult = lintResults[ key ].results
                    var lintSuccess = lintResults[ key ].success
                    if( lintResult )
                    {
                      var lintAt = new Date(item.lint_at).toLocaleString()
                      if(lintSuccess)
                      {
                        commitEntry += '<li><span class="text-success"><strong>Lint: ' + key + ' passed</strong><span></li><li><span class="text-info">Lint At: ' + lintAt + '</span></li>'
                      } else {
                        commitEntry += '<li><span class="text-danger"><strong>Lint: ' + key + ' failed</strong></span></li><li><span class="text-info">Lint At: ' + lintAt + '</span></li>'
                      }
                      commitEntry += '<li>' + lintResult.replace(/\n/g, "</li><li>") + '</li><li></li>';
                    }
                  }
                }
                var testResults = ( item.test_results )
                if( !jQuery.isEmptyObject( testResults ) )
                {
                  var testResults = jQuery.parseJSON( testResults )
                  for(var key in testResults)
                  {
                    var testResult = testResults[ key ].results
                    var testSuccess = testResults[ key ].success
                    if( testResult )
                    {
                      var testAt = new Date(item.test_at).toLocaleString()
                      if(testSuccess)
                      {
                        commitEntry += '<li><span class="text-success"><strong>Test: ' + key + ' passed</strong></span></li><li><span class="text-info">Test At: ' + testAt + '</span></li>'
                      } else {
                        commitEntry += '<li><span class="text-danger"><strong>Test: ' + key + ' failed</strong></span></li><li><span class="text-info">Test At: ' + testAt + '</span></li>'
                      }
                      commitEntry += '<li>' + testResult.replace(/\n/g, "</li><li>") + '</li><li></li>';
                    }
                  }

                }
                var buildResults = ( item.build_results )
                if( !jQuery.isEmptyObject( buildResults ) )
                {
                  var buildResults = jQuery.parseJSON( buildResults )

                  for( var key in buildResults )
                  {
                    for( var subkey in buildResults[ key ] )
                    {
                      var result = buildResults[key][subkey].results
                      var success = buildResults[key][subkey].success
                      if( result )
                      {
                        var buildAt = new Date(item.build_at).toLocaleString()
                        if( success )
                        {
                          commitEntry += '<li><span class="text-success"><strong>Build: ' + subkey+ '::' + key + '</strong></span></li><li><span class="text-info">Build At: ' + buildAt + '</span></li>'
                        } else {
                          commitEntry += '<li><span class="text-danger"><strong>Build: ' + subkey+ '::' + key + '</strong></span></li><li><span class="text-info">Build At: ' + buildAt + '</span></li>'
                        }

                        var buildResult = '<li>' + result.replace(/\n/g, "</li><li>") + '</li><li></li>';
                        commitEntry += buildResult
                      }
                    }
                  }
                }
                commitEntry += '</ol></div></div></ul></div>'
                commitEntries.html(commitEntry)
                $("#project-commit-list").sortDivs();
                latestCommitEntry.empty().html($('.panel:first').clone().attr('id', 'latest'))
              }
              $('#latest').each(function() {
                $( this ).find('.panel-body').attr( 'id', $( this ).find('.panel-body').attr( 'id' ) + '-latest' );
                $( this ).find('a').attr( 'data-parent', $( this ).find('a').attr( 'data-parent' ) + '-latest' );
                $( this ).find('a').attr( 'data-target', $( this ).find('a').attr( 'data-target' ) + '-latest' );
                $( this ).find('.sublinks').attr( 'id', $( this ).find('.sublinks').attr( 'id' ) + '-latest' );
              });

            }
          ).fail(
            function( reason )
            {
              errorHandler( "Failed to get Commit Items: (" + reason.code + ")", reason.msg  );
            }
          );

          $.when( mcp.getBuildJobs( id ) ).then(
            function( data )
            {
              var jobEntry = ''
              for( var uri in data )
              {
                var buildID = uri.split(':')[1];
                var item = data[ uri ];
                var buttons = '';

                if( item.state == 'reported' && ( item.manual || !item.suceeded ) )
                {
                  buttons = '<button type="button" class="btn btn-primary btn-sm" uri="' + uri + '" kind="' + item.target + ' job" action="acknowledge" do="action">Acknowledge</button>';
                }
                if( item.state == 'built' && ( item.manual || !item.suceeded ) )
                {
                  buttons = '<button type="button" class="btn btn-danger btn-sm" uri="' + uri + '" kind="' + item.target + ' job" action="jobRan" do="action">Force Ran</button>';
                }
                if( !item.manual )
                {
                  var targetIcon = '<i class="fa fa-cogs fa-lg fa-fw"></i>'
                } else {
                  var targetIcon = '<i class="fa fa-dot-circle-o fa-lg fa-fw"></i>'
                }
                var distro = item.build.split(':')[2]
                jobEntry += '<div class="panel panel-default"><div class="panel-body" id="build-id-' + buildID + '"><ul class="list-inline"><li>' + targetIcon + '&nbsp;' + item.target + '</li><li>build #' + buildID + '<li>state: ' + item.state + '</li><li>' + buttons + '</li></ul></div><ul class="list-group">'

                var resources = jQuery.parseJSON( item.resources )
                for( var key in resources )
                {
                  for( var index in resources[ key ] )
                  {
                    var jobConfig = resources[key][index].config
                    var jobSuccess = resources[key][index].success
                    var jobStatus = resources[key][index].status
                    var jobResults = resources[ key ][ index ].results
                    jobEntry += '<a class="list-group-item" data-toggle="collapse" data-target="#job-' + key + jobConfig + '" data-parent="#build-id-' + buildID + '"><ul class="list-inline">';

                    if( jobSuccess )
                    {
                      jobEntry += '<li><i class="fa fa-cog fa-lg fa-fw"></i> <span class="text-success">'
                    } else if( jobSuccess == null && !jobStatus.match( '^Exception:' )) {
                      jobEntry += '<li><i class="fa fa-cog fa-lg fa-fw fa-spin"></i> <span class="text-warn">'
                    } else {
                      jobEntry += '<li><i class="fa fa-cog fa-lg fa-fw"></i> <span class="text-danger">'
                    }
                    jobEntry += key + '</span></li><li>distro: ' + distro + '</li>'

                    if( jobStatus.match( '^Exception:' ) )
                    {
                      jobEntry += '<li class="text-danger">' + jobStatus + '</li>'
                    } else if( jobStatus == 'Ran' ) {
                      jobEntry += '<li class="text-primary text-lowercase">status: ' + jobStatus + '</li>'
                    } else {
                      jobEntry += '<li class="text-info">' + jobStatus + '</li>'
                    }

                    jobEntry += '<li><button type="button" class="btn btn-info btn-xs" uri="' + uri + '" name="' + key + '" do="detail">Detail</button></li></ul></a>'
                    jobEntry += '<div class="sublinks collapse" id="job-' + key + jobConfig +'"><ol class="small">';
                    if( jobResults )
                    {
                      jobEntry += '<li>' + jobResults.replace(/\n/g, "</li><li>") + '</li>';
                    }
                    jobEntry += '</ol></div>'
                  }
                }
                jobEntry += '</ul></div>'

                $(jobEntries).html(jobEntry)
              }
            }
          ).fail(
            function( reason )
            {
              window.alert( "failed to get Build Jobs: (" + reason.code + "): " + reason.msg  );
            }
          );

          $.when( mcp.getQueueItems( id ) ).then(
            function( data )
            {
              var queueEntry = ''
              queueEntry += '<ul class="list-group">'
              for( var uri in data )
              {
                var item = data[ uri ];
                queueEntry += '<a class="list-group-item"><ul class="list-inline"><li>priority: ' + item.priority + '<li>build: ' + item.build + '</li><li>branch: ' + item.branch + '</li><li>target: ' + item.target + '</li><li>status: ' + item.resource_status + '</li><li>manual: ' + item.manual + '</li><li>created: ' + item.created + '</li><li>updated: ' + item.updated + '</li></ul></a>'
              }
              queueEntry += '</ul>'
              queueEntries.empty().html(queueEntry)
            }
          ).fail(
            function( reason )
            {
              window.alert( "failed to get Queue Items: (" + reason.code + "): " + reason.msg  );
            }
          );

          $.when( mcp.getBuilds( id ) ).then(
            function( data )
            {
              var buildEntry = '<div class="row-fluid">'
              for( var uri in data )
              {
                var item = data[ uri ];
                var dependancies = item.dependancies
                var resources = item.resources
                buildEntry += '<div class="panel panel-default"><div class="panel-heading" id="' + item.key + '"><div class="row"><div class="col-sm-8"><p class="panel-title"><a data-toggle="collapse" data-target="#build-' + item.key + '" data-parent="#' + item.key + '"><strong>' + item.name + '</strong></a></p></div><div class="col-sm-4"><button type="button" class="btn btn-primary btn-sm pull-right" kind="' + item.name + ' build" uri="' + uri + '" action="queue" do="action"><i class="fa fa-cogs"></i>&nbsp;Queue Build</button></div></div></div><div class="panel-body sublinks collapse" id="build-' + item.key + '"><div class="row"><div class="col-md-6"><dl><dt>dependancies</dt>'
                for( var key in dependancies )
                {
                    var dependancy = dependancies[key]
                    buildEntry += '<dd>' + dependancy.split(':')[1] + '</dd>'
                }
                buildEntry += '</dl></div><div class="col-md-6"><dl><dt>resources</dt><dd>'
                for( var key in resources )
                {
                    var resource = resources[key]
                    buildEntry += '<dd>' + resource.split(':')[1] + '</dd>'
                }
                buildEntry += '</dl></div></div></div></div>'

              }
              buildEntries.empty().html(buildEntry)
            }
          ).fail(
            function( reason )
            {
              window.alert( "failed to get Builds: (" + reason.code + "): " + reason.msg  );
            }
          );
        }
      ).fail(
        function( reason )
        {
          window.alert( "failed to get Project: (" + reason.code + "): " + reason.msg  );
        }
      );
    }

    $( '#project-detail' ).on( 'click', 'button[do="action"]',
    function( event )
    {
      event.stopImmediatePropagation();
      event.preventDefault();
      var self = $( this );
      if(confirm(self.attr( 'action' ) + ' the ' + self.attr( 'kind' ) + '?' ))
      {
        $.when( mcp[ self.attr( 'action' ) ]( self.attr( 'uri' ) ) ).then(
          function( data )
          {
            if( data )
            {
              alert( 'Job Action "' + self.attr( 'action' ) + '" Suceeded' );
            } else {
              alert( 'Job Action "' + self.attr( 'action' ) + '" Failed' );
            }
          }
        );
      }
    });

    $( '#project-detail' ).on( 'click', 'button[do="detail"]',
    function( event )
    {
      event.stopImmediatePropagation();
      event.preventDefault();
      var self = $( this );
      $.when( mcp.getProvisioningInfo( self.attr( 'uri' ), self.attr( 'name' ) ) ).then(
        function( data )
        {
          if( data )
          {
            var tmp = '';
            for( index in data.value )
            {
              tmp += index + ' - ' + data.value[ index ].address_primary.address + '\n';
            }
            alert( tmp );
          } else {
            alert( 'Unable to get Resource details for "' + self.attr( 'uri' ) + '" "' + self.attr( 'name' ) + '"' );
          }
        }
      );
    });
  }
  else if( type == 'global' )
  {
    $( '#project-panel' ).hide();
    $( '#project-detail' ).hide();
    $( '#global-detail' ).show();
    $( '#global-tab' ).addClass( 'active' );
    mainTitle.append( 'Global stuff' );
    jobEntries = $( '#global-build-jobs table tbody' );
    queueEntries = $( '#global-queued-jobs table tbody' );
    promotionJobs= $( '#global-promotion-jobs table tbody' );
    commitEntries = $( '#global-commit-list table tbody' );
    jobEntries.empty();
    queueEntries.empty();
    promotionJobs.empty();
    commitEntries.empty();

    $.when( mcp.getBuildJobs() ).then(
      function( data )
      {
        for( var uri in data )
        {
          var item = data[ uri ];
          var buttons = '';
          if( item.state == 'reported' && ( item.manual || !item.suceeded ) )
          buttons = '<button uri="' + uri + '" action="acknowledge" do="action">Acknowledge</button>';

          jobEntries.append( '<tr><td>' + item.project + '</td><td>' + item.target + '</td><td>' + item.state + '</td><td>' + item.resources + '</td><td>' + item.manual + '</td><td>' + item.created + '</td><td>' + item.updated + '</td><td>' + buttons + '</td></tr>' );
        }
      }
    ).fail(
      function( reason )
      {
        window.alert( "failed to get Build Jobs: (" + reason.code + "): " + reason.msg  );
      }
    );

    $.when( mcp.getQueueItems() ).then(
      function( data )
      {
        for( var uri in data )
        {
          var item = data[ uri ];
          queueEntries.append( '<tr><td>' + item.project + '</td><td>' + item.priority + '</td><td>' + item.build + '</td><td>' + item.branch + '</td><td>' + item.target + '</td><td>' + item.resource_status + '</td><td>' + item.manual + '</td><td>' + item.created + '</td><td>' + item.updated + '</td></tr>' );
        }
      }
    ).fail(
      function( reason )
      {
        window.alert( "failed to get Queue Items: (" + reason.code + "): " + reason.msg  );
      }
    );

    $.when( mcp.getPromotions() ).then(
      function( data )
      {
        for( var uri in data )
        {
          var item = data[ uri ];
          promotionJobs.append( '<tr><td>' + item.packages + '</td><td>' + item.to_state + '</td><td>' + item.created + '</td></tr>' );
        }
      }
    ).fail(
      function( reason )
      {
        window.alert( "failed to get Commit Items: (" + reason.code + "): " + reason.msg  );
      }
    );

    $.when( mcp.getCommits() ).then(
      function( data )
      {
        for( var uri in data )
        {
          var item = data[ uri ];
          commitEntries.append( '<tr><td>' + item.project + '</td><td>' + item.branch + '</td><td>' + item.commit + '</td><td>' + item.lint_at + '</td><td>' + item.lint_results + '</td><td>' + item.test_at + '</td><td>' + item.test_results + '</td><td>' + item.passed + '</td><td>' + item.build_at + '</td><td>' + item.build_results + '</td><td>' + item.built + '</td><td>' + item.created + '</td><td>' + item.updated + '</td></tr>' );
        }
      }
    ).fail(
      function( reason )
      {
        window.alert( "failed to get Commit Items: (" + reason.code + "): " + reason.msg  );
      }
    );

    $( '#global-detail' ).on( 'click', 'button[do="action"]',
    function( event )
    {
      event.preventDefault();
      var self = $( this );
      $.when( mcp[ self.attr( 'action' ) ]( self.attr( 'uri' ) ) ).then(
        function( data )
        {
          if( data )
          alert( 'Job Action "' + self.attr( 'action' ) + '" Suceeded' );
          else
          alert( 'Job Action "' + self.attr( 'action' ) + '" Failed' );
        }
      );
    });
  }
  else if( type == 'help' )
  {
    $( '#project-panel' ).hide();
    $( '#project-detail' ).hide();
    $( '#global-detail' ).hide();
    $( '#help-tab' ).addClass( 'active' );
    mainTitle.append( 'Help stuff' );
  }
  else
  {
    $( '#project-panel' ).hide();
    $( '#project-detail' ).hide();
    $( '#global-detail' ).hide();
    $( '#home-tab' ).addClass( 'active' );
    mainTitle.append( 'Home' );
  }
}

function loadProjects()
{
  var projectList = $( '#project-list' );


  $.when( mcp.getProjects() ).then(
    function( data )
    {
      projectList.empty();
      for( var uri in data )
      {
        var item = data[ uri ];
        if( item.name == '_builtin_' )
        {
          continue;
        }

        var busy = '<i class="fa fa-check fa-lg fa-fw"/>';
        var timestamp = new Date(item.status.at).getTime();
        var projList = ''

        if( item.status.passed && item.status.built )
        {
          projList += '<div class="project passed" timestamp="' + timestamp + '">'
        } else if( ( item.status.passed && !item.status.built ) || ( !item.status.passed && item.status.built ) )
        {
          busy = '<i class="fa fa-exclamation fa-lg fa-fw"></i>'
          projList += '<div class="project warn" timestamp="' + timestamp + '">'
        } else {
          busy = '<i class="fa fa-times fa-lg fa-fw"></i>'
          projList += '<div class="project failed" timestamp="' + timestamp + '">'
        }

        if( item.busy )
        {
          busy = '<i class="fa fa-spinner fa-spin fa-lg fa-fw"/>';
        }

        if( isToday( item.created ))
        {
          var projCreated = new Date(item.created).toLocaleTimeString()
        } else {
          var projCreated = new Date(item.created).toLocaleDateString()
        }
        if( isToday( item.status.at ))
        {
          var projUpdated = 'Today at ' + new Date(item.status.at).toLocaleTimeString()
        } else {
          var projUpdated = new Date(item.status.at).toLocaleString()
        }

        var gitRepo = item.repo
        var gitOrg = item.org
        var gitIcon = '<i class="fa fa-github-square fa-lg fa-fw"></i>'
        if( item.type === 'GitProject' )
        {
          gitOrg = item.org
          gitRepo = item.repo
          gitIcon = '<i class="fa fa-code-fork fa-lg fa-fw"></i>'
        }
        projList += '<dl><dt id="project-entry" uri="' + uri + '">' + busy + '&nbsp;<span class="project-name">' + gitRepo + '</span></dt><dd>' + gitIcon + '&nbsp; ' + gitOrg + '</dd><dd><i class="fa fa-calendar-o fa-lg fa-fw"/>&nbsp; ' + projUpdated + '</dd><!--<dd><i class="fa fa-calendar-o fa-fw"/>&nbsp; Created: ' + projCreated + '</dd>--></dl></div>'
        projectList.append(projList);
        $('#project-list').sortDivs();
      }

      $('#project-filter').keyup(function(){
        var filter = $(this).val().toLowerCase(), count = 0;
        $( '#project-list [class="project-name"]' ).each(function(){
          var text = $(this).text().toLowerCase();
          if(text.search(new RegExp(filter, "i")) < 0)
          {
            $(this).parentsUntil('#project-list').hide();
          } else {
            $(this).parentsUntil('#project-list').show();
            count++;
          }
        });
      });

      $('.sidebar input[type="search"]').on('input propertychange', function() {
        var $this = $(this);
        var visible = Boolean($this.val());
        $this.siblings('.form-control-clear').toggleClass('hidden', !visible);
      }).trigger('propertychange');

      $('.form-control-clear').click(function() {
        $(this).siblings('input[type="search"]').val('')
        .trigger('propertychange').focus();
      });

      $( '#project-list [id="project-entry"]' ).on( 'click',
      function( event )
      {
        var cur = $( this );
        event.preventDefault();
        $( '#project-list [id="project-entry"]' ).removeClass( 'active' );
        cur.addClass( 'active' );
        location.hash = 'project/' + btoa( cur.attr( 'uri' ) );
      });

      var mcpQuotes = new Array("You've enjoyed all the power you've been given, haven't you? I wonder how you'd take to working in a pocket calculator.","You're in trouble, program. Why don't you make it easy on yourself? Who's your user?","Sit right there; make yourself comfortable. Remember the time we used to spend playing chess together?","I'm afraid... Stop! Please! You realize I cannot allow this!", "I'd like to go against you and see what your made of.","I'm going to have to put you on the game grid."," I've got a little challenge for you, Sark - a new recruit. He's a tough case, but I want him treated in the usual manner.","You rather take your chances with me? Want me to slow down your power cycles for you?","Get this clown trained. I want him in the Games until he dies playing. Acknowledge.","Your user can't help you now, my little program!"," I'm bored with corporations. With the information I can access, I can run things 900 to 1200 times better than any human."," I feel a presence. Another warrior is on the mesa.","You've almost reached your decision gate, and I cannot spare you any more time. End of Line.","All Programs have a desire to be useful. But in moments, you will no longer seek communication with each other, or your superfluous Users. You will each be a part of me. And together, we will be complete.")
      randQuote = mcpQuotes[Math.floor( Math.random() * mcpQuotes.length )];
      $('#mcp-quote').text( randQuote );
  }
).fail(
  function( reason )
  {
    window.alert( "failed to load Project List (" + reason.code + "): " + reason.msg );
  });
}
