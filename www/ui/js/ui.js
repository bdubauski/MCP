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

  if( type == 'project' )
  {
    $( '#project-panel' ).show();
    loadProjects();
    if( id !== undefined )
    {
      $( '#project-tab' ).addClass( 'active' );
      $.when( mcp.getObject( id ) ).then(
        function( data )
        {
          data = data.detail;
          if( data.type == 'GitHubProject' )
            mainTitle.append( '<a href="https://github.emcrubicon.com/' + data.org + '" target="_blank">' + data.org + '</a> / <a href="https://github.emcrubicon.com/' + data.org + '/' + data.repo + '" target="_blank">' + data.repo + '</a> <i class="fa fa-github fa-fw"/> <img src="ui/image/build-pass.svg" />' );
          else if( data.type == 'GitProject' )
            mainTitle.append( '<a href="' + data.upstream_git_url + '" target="_blank">' + data.upstream_git_url + '</a> <img src="ui/image/build-pass.svg" />' );
          else
            mainTitle.append( data.name + ' <img src="ui/image/build-pass.svg" />' );
        }
      ).fail(
        function( reason )
        {
          window.alert( "failed to get project: (" + reason.code + "): " + reason.msg  );
        }
      );
    }
  }
  else if( type == 'global' )
  {
    $( '#project-panel' ).hide();
    $( '#global-tab' ).addClass( 'active' );
    mainTitle.append( 'Global stuff' );
  }
  else if( type == 'help' )
  {
    $( '#project-panel' ).hide();
    $( '#help-tab' ).addClass( 'active' );
    mainTitle.append( 'Help stuff' );
  }
  else
  {
    $( '#project-panel' ).hide();
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
        item = data[ uri ];
        if( item.name == '_builtin_' )
          continue;

        if( item.busy )
          busy = '<i class="fa fa-tasks fa-fw"/>';
        else
          busy = '<i class="fa fa-check fa-fw"/>';

        projectList.append( '<div class="project passed"><dl><dt id="project-entry" uri="' + uri + '">' + busy + '&nbsp;' + item.name + '</dt><dd><i class="fa fa-clock-o fa-fw"/>&nbsp; Updated: ' + item.updated + '</dd><dd><i class="fa fa-calendar-o fa-fw"/>&nbsp; Created: ' + item.created + '</dd></dl></div>' );
      }

      $( '#project-list [id="project-entry"]' ).on( 'click',
        function( event )
        {
          cur = $( this );
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
