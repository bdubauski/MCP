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
      type = 'home';
    else
      type = hash.substr( 1 );
  }
  else
  {
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
      jobEntries = $( '#project-build-jobs table tbody' );
      queueEntries = $( '#project-queued-jobs table tbody' );
      commitEntries = $( '#project-commit-list table tbody' );
      buildEntries = $( '#project-builds table tbody' );
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
            buildPass += '<img src="/ui/image/test-pass.svg" />';
          else
            buildPass += '<img src="/ui/image/test-error.svg" />';

          if( data.status.built )
            buildPass += '<img src="/ui/image/build-pass.svg" />';
          else
            buildPass += '<img src="/ui/image/build-error.svg" />';

          if( data.type == 'GitHubProject' )
            mainTitle.append( '<a href="https://github.emcrubicon.com/' + data.org + '" target="_blank">' + data.org + '</a> / <a href="https://github.emcrubicon.com/' + data.org + '/' + data.repo + '" target="_blank">' + data.repo + '</a> <i class="fa fa-github fa-fw"/>' + buildPass );
          else if( data.type == 'GitProject' )
            mainTitle.append( '<a href="' + data.upstream_git_url + '" target="_blank">' + data.upstream_git_url + '</a>' + buildPass );
          else
            mainTitle.append( data.name + buildPass );

          $.when( mcp.getBuildJobs( id ) ).then(
            function( data )
            {
              for( var uri in data )
              {
                var item = data[ uri ];
                var buttons = '';
                if( item.state == 'reported' && ( item.manual || !item.suceeded ) )
                  buttons = '<button uri="' + uri + '" action="acknowledge" do="action">Acknowledge</button>';

                var status = '<ul>';
                var resources = jQuery.parseJSON( item.resources )
                for( var key in resources )
                {
                  status += '<li><span class="label label-default">' + key + '</span><button uri="' + uri + '" name="' + key + '" do="detail">Detail</button><ul>';
                  for( var index in resources[ key ] )
                  {
                    status += '<li>';
                    if( resources[ key ][ index ].success )
                      status += '<span class="label label-success">Success</span>';
                    
                    if( resources[ key ][ index ].status.match( '^Exception:' ) )
                      status += '<span class="label label-danger">' + resources[ key ][ index ].status + '</span>';
                    else if( resources[ key ][ index ].status == 'Ran' )
                      status += '<span class="label label-primary">Ran</span>';
                    else
                      status += '<span class="label label-info">' + resources[ key ][ index ].status + '</span>';
                    if( resources[ key ][ index ].results )
                      status += '<pre>' + resources[ key ][ index ].results + '</pre>';
                    status += '</li>';
                  }
                  status += '</ul></li>';
                }
                status += '<ul>';

                jobEntries.append( '<tr><td>' + item.target + '</td><td>' + item.state + '</td><td>' + status + '</td><td>' + item.manual + '</td><td>' + item.created + '</td><td>' + item.updated + '</td><td>' + buttons + '</tr>' );
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
              for( var uri in data )
              {
                var item = data[ uri ];
                queueEntries.append( '<tr><td>' + item.priority + '</td><td>' + item.build + '</td><td>' + item.branch + '</td><td>' + item.target + '</td><td>' + item.resource_status + '</td><td>' + item.manual + '</td><td>' + item.created + '</td><td>' + item.updated + '</td></tr>' );
              }
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
                commitEntries.append( '<tr><td>' + item.branch + '</td><td>' + item.commit + '</td><td>' + item.lint_at + '</td><td>' + item.lint_results + '</td><td>' + item.test_at + '</td><td>' + item.test_results + '</td><td>' + item.passed + '</td><td>' + item.build_at + '</td><td>' + item.build_results + '</td><td>' + item.built + '</td><td>' + item.created + '</td><td>' + item.updated + '</td></tr>' );
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
              for( var uri in data )
              {
                var item = data[ uri ];
                buildEntries.append( '<tr><td>' + item.name + '</td><td><button uri="' + uri + '" action="queue" do="action">Queue</button></td></tr>' );
              }
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
            alert( 'Job Action "' + self.attr( 'action' ) + '" Suceeded' );
          else
            alert( 'Job Action "' + self.attr( 'action' ) + '" Failed' );
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
          }
          else
            alert( 'Unable to get Resource details for "' + self.attr( 'uri' ) + '" "' + self.attr( 'name' ) + '"' );
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
          continue;

        var busy = '<i class="fa fa-check fa-fw"/>';

        if( item.busy )
          busy = '<i class="fa fa-tasks fa-fw"/>';

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
