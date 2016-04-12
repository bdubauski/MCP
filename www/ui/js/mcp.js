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

    mcp.logout = function()
    {
       cinp.call( '/api/v1/Auth(logout)', { 'token': cinp.auth_token } );
    };

    mcp.keepalive = function()
    {
       cinp.call( '/api/v1/Auth(keepalive)', {} );
    };

    mcp.permissions = function()
    {
       var deferred = $.Deferred();

       $.when( cinp.call( '/api/v1/Auth(permissions)', {} ) ).then(
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

    mcp.getProfile = function()
    {
       var deferred = $.Deferred();

       $.when( cinp.call( '/api/v1/Users(getProfile)', {} ) ).then(
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

    mcp.updateProfile = function( slack_handle )
    {
       var deferred = $.Deferred();

       $.when( cinp.call( '/api/v1/Users(updateProfile)', { 'slack_handle': slack_handle } ) ).then(
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

    mcp.selfRegister = function( github_username, github_password )
    {
       var deferred = $.Deferred();

       $.when( cinp.call( '/api/v1/Users(selfRegister)', { 'github_username': github_username, 'github_password': github_password } ) ).then(
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

      $.when( cinp.list( '/api/v1/Project/Project', 'my_projects', null, 0, 100 ) ).then(
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


    mcp.getProvisioningInfo = function( job, name )
    {
      var deferred = $.Deferred();

      $.when( cinp.call( job + '(getProvisioningInfo)', { name: name } ) ).then(
        function( data )
        {
          deferred.resolve( data.result );
        }
      ).fail(
        function( reason )
        {
          deferred.reject( reason );
        }
      );

      return deferred.promise();
    };

    mcp.jobRan = function( build )
    {
      var deferred = $.Deferred();

      $.when( cinp.call( build + '(jobRan)', {} ) ).then(
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
          alert( 'Error Setting to Ran "' + build + '"' );
          cinp.on_server_error( reason );
        }
      );

      return deferred.promise();
    };

    mcp.acknowledge = function( build )
    {
      var deferred = $.Deferred();

      $.when( cinp.call( build + '(acknowledge)', {} ) ).then(
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
          alert( 'Error Acknowledging "' + build + '"' );
          cinp.on_server_error( reason );
        }
      );

      return deferred.promise();
    };

    mcp.queue = function( uri )
    {
      var deferred = $.Deferred();

      $.when( cinp.call( '/api/v1/Processor/QueueItem(queue)', { 'build': uri } ) ).then(
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
