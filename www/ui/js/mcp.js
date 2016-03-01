var mcpBuilder = {};
( function()
{
  "use strict";
  mcpBuilder = function( cinp )
  {
    var mcp = { cinp: cinp };

    mcp.login = function( username, password )
    {
      var deferred = $.Deferred();

      $.when( cinp.call( '/api/v1/Auth(login)', { 'username': username, 'password': password } ) ).then(
        function( data )
        {
          deferred.resolve( data.result.value );
        }
      ).fail(
        function( reason )
        {
          deferred.reject( reason );
        }
      );

      return deferred.promise();
    };

    mcp.logout = function( username, token )
    {
       cinp.call( '/api/v1/Auth(logout)', { 'username': username, 'token': token } );
    };

    mcp.keepalive = function()
    {
       cinp.call( '/api/v1/Auth(keepalive)', {} );
    };

    mcp.getObject = function( uri )
    {
      var deferred = $.Deferred();
      $.when( cinp.get( uri ) ).then(
        function( data )
        {
          deferred.resolve( data );
        }
      ).fail(
        function( reason )
        {
          deferred.reject( reason );
        }
      );

      return deferred.promise();
    };

    mcp.getProjects = function()
    {
      var deferred = $.Deferred();

      $.when( cinp.list( '/api/v1/Project/Project', null, null, 0, 100 ) ).then(
        function( data )
        {
          $.when( cinp.getObjects( data.list, null, 100 ) ).then(
            function( data )
            {
              deferred.resolve( data );
            }
          ).fail(
            function( reason )
            {
              deferred.reject( reason );
            }
          );
        }
      ).fail(
        function( reason )
        {
          deferred.reject( reason );
        }
      );

      return deferred.promise();
    };

    mcp.getBuildJobs = function( project )
    {
      var deferred = $.Deferred();
      var filter;
      var values;

      if( project )
      {
        filter = 'project';
        values = { project: project };
      }

      $.when( cinp.list( '/api/v1/Processor/BuildJob', filter, values ) ).then(
        function( data )
        {
          $.when( cinp.getObjects( data.list, null, 100 ) ).then(
            function( data )
            {
              deferred.resolve( data );
            }
          ).fail(
            function( reason )
            {
              deferred.reject( reason );
            }
          );
        }
      ).fail(
        function( reason )
        {
          deferred.reject( reason );
        }
      );

      return deferred.promise();
    };

    mcp.getQueueItems = function( project )
    {
      var deferred = $.Deferred();
      var filter;
      var values;

      if( project )
      {
        filter = 'project';
        values = { project: project };
      }

      $.when( cinp.list( '/api/v1/Processor/QueueItem', filter, values ) ).then(
        function( data )
        {
          $.when( cinp.getObjects( data.list, null, 100 ) ).then(
            function( data )
            {
              deferred.resolve( data );
            }
          ).fail(
            function( reason )
            {
              deferred.reject( reason );
            }
          );
        }
      ).fail(
        function( reason )
        {
          deferred.reject( reason );
        }
      );

      return deferred.promise();
    };

    mcp.getCommits = function( project )
    {
      var deferred = $.Deferred();
      var filter;
      var values;

      if( project )
      {
        filter = 'project';
        values = { project: project };
      }
      else
      {
        filter = 'in_process';
        values = {};
      }

      $.when( cinp.list( '/api/v1/Project/Commit', filter, values ) ).then(
        function( data )
        {
          $.when( cinp.getObjects( data.list, null, 100 ) ).then(
            function( data )
            {
              deferred.resolve( data );
            }
          ).fail(
            function( reason )
            {
              deferred.reject( reason );
            }
          );
        }
      ).fail(
        function( reason )
        {
          deferred.reject( reason );
        }
      );

      return deferred.promise();
    };

    mcp.getPromotions = function()
    {
      var deferred = $.Deferred();

      $.when( cinp.list( '/api/v1/Processor/Promotion' ) ).then(
        function( data )
        {
          $.when( cinp.getObjects( data.list, null, 100 ) ).then(
            function( data )
            {
              deferred.resolve( data );
            }
          ).fail(
            function( reason )
            {
              deferred.reject( reason );
            }
          );
        }
      ).fail(
        function( reason )
        {
          deferred.reject( reason );
        }
      );

      return deferred.promise();
    };

    mcp.getBuilds = function( project )
    {
      var deferred = $.Deferred();
      var filter;
      var values;

      if( project )
      {
        filter = 'project';
        values = { project: project };
      }

      $.when( cinp.list( '/api/v1/Project/Build', filter, values ) ).then(
        function( data )
        {
          $.when( cinp.getObjects( data.list, null, 100 ) ).then(
            function( data )
            {
              deferred.resolve( data );
            }
          ).fail(
            function( reason )
            {
              deferred.reject( reason );
            }
          );
        }
      ).fail(
        function( reason )
        {
          deferred.reject( reason );
        }
      );

      return deferred.promise();
    };

    mcp.acknowledge = function( uri )
    {
      var deferred = $.Deferred();

      $.when( cinp.call( uri + '(acknowledge)', {} ) ).then(
        function( data )
        {
          if( data.result )
            deferred.resolve( true );
          else
            deferred.resolve( false );
        }
      ).fail(
        function( reason )
        {
          alert( 'Error Acknowledging "' + uri + '"' );
          cinp.on_server_error( reason );
        }
      );

      return deferred.promise();
    };

    mcp.queue = function( uri )
    {
      var deferred = $.Deferred();

      $.when( cinp.call( '/api/v1/Processor/QueueItem(queue)', { 'build': uri} ) ).then(
        function( data )
        {
          if( data.result )
            deferred.resolve( true );
          else
            deferred.resolve( false );
        }
      ).fail(
        function( reason )
        {
          alert( 'Error Queueing "' + uri + '"' );
          cinp.on_server_error( reason );
        }
      );

      return deferred.promise();
    };

    return mcp;
  };
} )();
