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

    mcp.getProjects = function()
    {
      var deferred = $.Deferred();

      $.when( cinp.list( '/api/v1/Project/GitHubProject' ) ).then(
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

    return mcp;
  };
} )();
