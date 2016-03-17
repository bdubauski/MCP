var mcp;

$( document ).ready(
  function ()
  {
    var cinp = cinpBuilder();
    cinp.setHost( 'http://mcp.lab.stgr01.monilytics.net' );
    cinp.on_server_error = errorHandler;

    mcp = mcpBuilder( cinp );

    $( 'body' ).on( 'click', '#modalbox.a.close-link',
    function( event )
    {
      event.preventDefault();
      closeModalBox();
    });

    $( '#home-tab' ).addClass( 'active' );
    $( '#project-panel' ).hide();
    $( window ).on( 'hashchange', hashChange );
    hashChange();
  }
);

function openModalBox( header, inner, bottom )
{
  var modalbox = $( '#modalbox' );
  modalbox.find( '.modal-header-name span' ).html( header );
  modalbox.find( '.devoops-modal-inner' ).html( inner );
  modalbox.find( '.devoops-modal-bottom' ).html( bottom );
  modalbox.fadeIn( 'fast' );
  $( 'body' ).addClass( 'body-expanded' );
}

function closeModalBox()
{
  var modalbox = $( '#modalbox' );
  modalbox.fadeOut( 'fast', function()
  {
    modalbox.find( '.modal-header-name span' ).children().remove();
    modalbox.find( '.devoops-modal-inner' ).children().remove();
    modalbox.find( '.devoops-modal-bottom' ).children().remove();
    $( 'body' ).removeClass( 'body-expanded' );
  });
}

function errorHandler( msg, stack_trace )
{
  openModalBox( msg, '<pre>' + stack_trace + '</pre>', '' );
}

function hashChange( event )
{
  var mainTitle = $( '#main-title' );
  mainTitle.empty();
  $( '#home-tab' ).removeClass( 'active' );
  $( '#project-tab' ).removeClass( 'active' );
  $( '#global-tab' ).removeClass( 'active' );
  $( '#help-tab' ).removeClass( 'active' );

  var hash = location.hash;
  var pos = hash.indexOf( '/' );
  var type = 'home';
  var id;

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
  }

  var jobEntries;
  var queueEntries;
  var promotionJobs;
  var commitEntries;
  var buildEntries;

  if( type == 'project' )
  {
    $( '#project-panel' ).show();
    $( '#project-detail' ).show();
    $( '#global-detail' ).hide();
    $( '#project-tab' ).addClass( 'active' );
    loadProjects();
    if( id )
    {
      jobEntries = $( '#project-build-jobs' );
      queueEntries = $( '#project-queued-jobs' );
      commitEntries = $( '#project-commit-list' );
      buildEntries = $( '#project-builds' );
      jobEntries.empty();
      queueEntries.empty();
      commitEntries.empty();
      buildEntries.empty();

      $.when( mcp.getObject( id ) ).then(
        function( data )
        {
          data = data.detail;
          var buildPass = '';
          if( data.status.passed )
          {
            buildPass += '<img src="/ui/image/test-pass.svg" /> ';
          } else {
            buildPass += '<img src="/ui/image/test-error.svg" /> ';
          }

          if( data.status.built )
          {
            buildPass += '<img src="/ui/image/build-pass.svg" />';
          } else {
            buildPass += '<img src="/ui/image/build-error.svg" />';
          }
          if( data.type == 'GitHubProject' )
          {
            mainTitle.append( '<a href="https://github.emcrubicon.com/' + data.org + '" target="_blank">' + data.org + '</a> / <a href="https://github.emcrubicon.com/' + data.org + '/' + data.repo + '" target="_blank">' + data.repo + '</a> <i class="fa fa-github fa-fw"/>' + buildPass );
          } else if( data.type == 'GitProject' ) {
            mainTitle.append( '<a href="' + data.upstream_git_url + '" target="_blank">' + data.upstream_git_url + '</a>' + buildPass );
          } else {
            mainTitle.append( data.name + buildPass );
          }

          $.when( mcp.getBuildJobs( id ) ).then(
            function( data )
            {
              for( var uri in data )
              {
                var item = data[ uri ];
                var buttons = '';
                var jobEntry = ''
                if( item.state == 'reported' && ( item.manual || !item.suceeded ) )
                {
                  buttons = '<button type="button" class="btn btn-primary btn-sm" uri="' + uri + '" action="acknowledge" do="action">Acknowledge</button>';
                }
                jobEntry += '<div class="panel panel-default"><div class="panel-body" id="' + item.target + '"><ul class="list-inline"><li><i class="fa fa-dot-circle-o fa-lg fa-fw"></i> ' + item.target + '</li><li>state: ' + item.state + '</li><li>manual: ' + item.manual + '</li><li>' + buttons + '</li></ul></div><ul class="list-group">'

                var resources = jQuery.parseJSON( item.resources )
                for( var key in resources )
                {
                  for( var index in resources[ key ] )
                  {
                    var jobConfig = resources[key][index].config
                    jobEntry += '<a class="list-group-item" data-toggle="collapse" data-target="#job-' + key + jobConfig + '" data-parent="#' + item.target + '"><ul class="list-inline">';

                    if( resources[ key ][ index ].success )
                    {
                      jobEntry += '<li class="text-success"><strong>' + key + '</strong></li>'
                    } else {
                      jobEntry += '<li class="text-danger"><strong>' + key + '</strong></li>'
                    }
                    jobEntry += '<li>config #' + jobConfig + '</li>'
                    if( resources[ key ][ index ].status.match( '^Exception:' ) )
                    {
                      jobEntry += '<li class="text-danger">' + resources[ key ][ index ].status + '</li>'
                    } else if( resources[ key ][ index ].status == 'Ran' ) {
                      jobEntry += '<li class="text-primary text-lowercase">status: ' + resources[ key ][ index ].status + '</li>'
                    } else {
                      jobEntry += '<li class="text-info">' + resources[ key ][ index ].status + '</li>'
                    }
                    jobEntry += '<li><button type="button" class="btn btn-info btn-xs" uri="' + uri + '" name="' + key + '" do="detail">Detail</button></li></ul></a>'
                    jobEntry += '<div class="sublinks collapse" id="job-' + key + jobConfig +'"><ol class="small">';
                    if( resources[ key ][ index ].results )
                    {
                      jobEntry += '<li>' + resources[ key ][ index ].results.replace(/\n/g, "</li><li>") + '</li>';
                    }
                    jobEntry += '</ol></div>'
                  }
                }
                jobEntry += '</ul></div>'
                jobEntries.append(jobEntry)
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
              queueEntries.append(queueEntry)
            }
          ).fail(
            function( reason )
            {
              window.alert( "failed to get Queue Items: (" + reason.code + "): " + reason.msg  );
            }
          );

          $.when( mcp.getCommits( id ) ).then(
            function( data )
            {
              for( var uri in data )
              {
                var item = data[ uri ];
                var commit = item.commit
                var buildResult = ''
                commitEntry = ""
                if( item.passed === 'true' && item.built === 'true' )
                {
                  commitEntry += '<div class="panel panel-success"><div class="panel-body" id="commit-' + commit + '"><ul class="list-inline"><li class="text-success"><strong><i class="fa fa-code-fork fa-fw"></i> ' + commit + '</strong></li>'
                } else {
                  commitEntry += '<div class="panel panel-danger"><div class="panel-body" id="commit-' + commit + '"><ul class="list-inline"><li class="text-danger"><strong><i class="fa fa-code-fork fa-fw"></i> ' + commit + '</strong></li>'
                }
                commitEntry += '<li>Build Created: ' + new Date(item.created).toLocaleString() + '</li></ul></div><ul class="list-group"><a class="list-group-item" data-toggle="collapse" data-target="#build-' + commit + key + subkey + '" data-parent="#commit-' + commit + '"><ul class="list-inline text-muted"><li>branch: ' + item.branch + '</li>'
                if( item.passed === 'true' )
                {
                  commitEntry += '<li>passed: <span class="text-success">' + item.passed + '</span></li>'
                } else if( item.passed === 'false') {
                  commitEntry += '<li>passed: <span class="text-danger">' + item.passed + '</span></li>'
                } else {
                  commitEntry += '<li>passed: <span>' + item.passed + '</span></li>'
                }
                if( item.built === 'true' )
                {
                  commitEntry += '<li>built: <span class="text-success">' + item.built + '</span></li>'
                } else if( item.built === 'false') {
                  commitEntry += '<li>built: <span class="text-danger">' + item.built + '</span></li>'
                } else {
                  commitEntry += '<li>built: <span>' + item.passed + '</span></li>'
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
                    var lintAt = new Date(item.lint_at).toLocaleString()
                    {
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
                    var testAt = new Date(item.test_at).toLocaleString()
                    {
                      if(testSuccess)
                      {
                        commitEntry += '<li><span class="text-success"><strong>Test: ' + key + ' passed</strong></span></li><li><span class="text-info">Lint At: ' + testAt + '</span></li>'
                      } else {
                        commitEntry += '<li><span class="text-danger"><strong>Test: ' + key + ' failed</strong></span></li><li><span class="text-info">Lint At: ' + testAt + '</span></li>'
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
                commitEntries.append(commitEntry);
              }
            }
          ).fail(
            function( reason )
            {
              window.alert( "failed to get Commit Items: (" + reason.code + "): " + reason.msg  );
            }
          );

          $.when( mcp.getBuilds( id ) ).then(
            function( data )
            {
              var buildEntry = ''
              buildEntry += '<ul class="list-group">'
              for( var uri in data )
              {
                var item = data[ uri ];
                buildEntry += '<a class="list-group-item"><ul class="list-inline"><li><strong>' + item.name + '</strong></li><li><button type="button" class="btn btn-primary btn-sm" uri="' + uri + '" action="queue" do="action">Queue</button></li></ul></a>'
              }
              buildEntry += '</ul>'
              buildEntries.append(buildEntry)
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
      event.preventDefault();
      var self = $( this );
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
    });

    $( '#project-detail' ).on( 'click', 'button[do="detail"]',
    function( event )
    {
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

  projectList.empty();
  $.when( mcp.getProjects() ).then(
    function( data )
    {
      for( var uri in data )
      {
        var item = data[ uri ];
        if( item.name == '_builtin_' )
        {
          continue;
        }

        var busy = '<i class="fa fa-check fa-fw"/>';

        if( item.busy )
        {
          busy = '<i class="fa fa-spinner fa-spin fa-fw"/>';
        }
        projectList.append( '<div class="project passed"><dl><dt id="project-entry" uri="' + uri + '">' + busy + '&nbsp;' + item.name + '</dt><dd><i class="fa fa-clock-o fa-fw"/>&nbsp; Updated: ' + item.updated + '</dd><dd><i class="fa fa-calendar-o fa-fw"/>&nbsp; Created: ' + item.created + '</dd></dl></div>' );
      }

      $( '#project-list [id="project-entry"]' ).on( 'click',
      function( event )
      {
        var cur = $( this );
        event.preventDefault();
        $( '#project-list [id="project-entry"]' ).removeClass( 'active' );
        cur.addClass( 'active' );
        location.hash = 'project/' + btoa( cur.attr( 'uri' ) );
      }
    );
  }
).fail(
  function( reason )
  {
    window.alert( "failed to load Project List (" + reason.code + "): " + reason.msg );
  }
);
}
