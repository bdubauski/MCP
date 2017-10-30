var cinpBuilder = {};
( function()
{
  "use strict";

  cinpBuilder = function()
  {
    var cinp = { host: '',
                  auth_id: '',
                  auth_token: '',
                  on_server_error: null };

    cinp.server_error = function( data, type )
    {
      if( type == 'application/json' )
      {
        data = JSON.parse( data );
        if( this.on_server_error !== null )
          this.on_server_error( data.msg, data.trace );
        else
          console.error( 'Server Error: "' + data.msg + '"' );
      }
      else
      {
        if( this.on_server_error !== null )
          this.on_server_error( '', data );
        else
          console.error( 'Server Error (Not JSON Encoded)' );
      }
    };

    cinp.makeRequest = function( method, uri, data, headers )
    {
      if( this.auth_id )
        headers = $.extend( {}, headers, { 'Auth-Id': this.auth_id, 'Auth-Token': this.auth_token } );

      return {
        type: method,
        url: this.host + uri,
        dataType: 'json',
        headers: $.extend( {}, headers,
        {
          'CInP-Version': '0.1'
        } ),
        data: JSON.stringify( data ),
        contentType: 'application/json',
        processData: false,
      };
    };

    cinp.setHost = function( host )
    {
      this.host = host;
    };

    cinp.setAuth = function( id, token )
    {
      this.auth_id = id;
      this.auth_token = token;
    };

    cinp.extractIds = function( uri_list )
    {
      var result = [];
      for( var i = 0; i < uri_list.length; i++ )
      {
        var uri = uri_list[ i ];
        result.push( uri.substring( uri.indexOf( ':', uri.lastIndexOf( '/' ) ) + 1, uri.lastIndexOf( ':' ) ) );
      }
      return result;
    };

    cinp.buildMultiIdURI = function( uri, id_list ) // uri must have the :: in it, if it allready has a id between the ::, that will be removed and replaced with the id list
    {
      var prefix = uri.substr( 0, uri.indexOf( ':', uri.lastIndexOf( '/' ) ) );
      var postfix =  uri.substr( uri.lastIndexOf( ':' ) + 1 );

      return prefix + ':' + id_list.join( ':' ) + ':' + postfix;
    };

    cinp.describe = function( uri )
    {
      var deferred = $.Deferred();

      var request = this.makeRequest( 'DESCRIBE', uri );

      console.info( 'Describe: "' + request.url + '"' );

      var req = $.ajax( request );

      req.done(
        function( data, status, xhr )
        {
          type = xhr.getResponseHeader( 'Type' );
          if( type == 'namespace' )
            deferred.resolve( { type: 'namespace', doc: data.doc, children: data.children, models: data.models, api_version: data['api-version'], protocol_version: data['protocol-version'] } );
          else if( type == 'model' ) // TODO: sanintise the fields too
            deferred.resolve( { type: 'model', doc: data.doc, constants: data.constants, fields: data.fields, actions: data.actions, list_filters: data['list-filters'] } );
          else if( type == 'action' )
            deferred.resolve( { type: 'action', doc: data.doc, paramater_list: data['paramater-list'], static: data.static, return_type: data['return-type'] } );
          else
            deferred.resolve( {} );
        }
      ).fail(
        function( xhr )
        {
          console.error( 'Describe: (' + xhr.status + '): "' + request.url + '"' );
          if( xhr.status == 500 )
          {
            this.server_error( xhr.responseText, xhr.getResponseHeader( 'Content-Type' ) );
            deferred.reject( { msg: 'Server Error' } );
          }
          else
          {
            deferred.reject( { msg: xhr.responseJSON.msg, code: xhr.status } );
          }
        }.bind( this )
      );

      return deferred.promise();
    };

    cinp.list = function( uri, filter, values, position, count )
    {
      var deferred = $.Deferred();

      var request = this.makeRequest( 'LIST', uri, { 'filter': filter, 'values': values }, { 'Position': position, 'Count': count } );

      console.info( 'List: "' + request.url + '"' );

      var req = $.ajax( request );

      req.done(
        function( data )
        {
          deferred.resolve( { list: data } );
        }
      ).fail(
        function( xhr )
        {
          console.error( 'List: (' + xhr.status + '): "' + request.url + '"' );
          if( xhr.status == 500 )
          {
            this.server_error( xhr.responseText, xhr.getResponseHeader( 'Content-Type' ) );
            deferred.reject( { msg: 'Server Error' } );
          }
          else
          {
            deferred.reject( { msg: xhr.responseJSON.msg, code: xhr.status } );
          }
        }.bind( this )
      );

      return deferred.promise();
    };

    cinp.get = function( uri )
    {
      var deferred = $.Deferred();

      var request = this.makeRequest( 'GET', uri );

      console.info( 'Get: "' + request.url + '"' );

      var req = $.ajax( request );

      req.done(
        function( data, status, xhr )
        {
          deferred.resolve( { detail: data, multi_object: xhr.getResponseHeader( 'Multi-Object' ) } );
        }
      ).fail(
        function( xhr )
        {
          console.error( 'Get: (' + xhr.status + '): "' + request.url + '"' );
          if( xhr.status == 500 )
          {
            this.server_error( xhr.responseText, xhr.getResponseHeader( 'Content-Type' ) );
            deferred.reject( { msg: 'Server Error' } );
          }
          else
          {
            deferred.reject( { msg: xhr.responseJSON.msg, code: xhr.status } );
          }
        }.bind( this )
      );

      return deferred.promise();
    };

    // if uri_list is an array id_list is ignored, otherwise uri_list is used as the uri template for the id_list
    cinp.getObjects = function( uri_list, id_list, chunk_size )
    {
      var deferred = $.Deferred();

      var result = {};
      var uri = '';
      var error = false;
      var score_card = [];

      if( uri_list instanceof Array )
      {
        uri = uri_list[0];
        id_list = this.extractIds( uri_list );
      }
      else
        uri = uri_list;

      var onSucess = function( data, index )
      {
        score_card[ index ] = true;
        if( !error )
        {
          $.extend( result, data.detail );

          var done = true;
          for( var i = 0; i < score_card.length; i++ )
            done &= score_card[ i ];

          if( done )
            deferred.resolve( result );
          else
          {
            var count = 0;
            for( i = 0; i < score_card.length; i++ )
              if( score_card[ i ] )
                count++;

            deferred.notify( count / chunk_count );
          }
        }
      };
      var onError = function( error )
      {
        error = true;
        deferred.reject( error );
      };

      var chunk_count = Math.ceil( id_list.length / chunk_size );

      for( var i = 0; i < chunk_count; i++ )
      {
        score_card.push( false );
        (function( i, cinp )
        {
          cinp.get( cinp.buildMultiIdURI( uri, id_list ) ).then(
            function( data )
            {
              if( data.multi_object == 'False' )
              {
                var detail = data.detail;
                data.detail = {};
                data.detail[ uri ] = detail;
              }
              onSucess( data, i );
            }, onError );
        })( i, this );
      }

      return deferred.promise();
    };

    cinp.create = function( uri, values )
    {
      var deferred = $.Deferred();

      var request = this.makeRequest( 'CREATE', uri, values );

      console.info( 'Create: "' + request.url + '"' );

      var req = $.ajax( request );

      req.done(
        function( data, status, xhr )
        {
          deferred.resolve( { detail: data, multi_object: xhr.getResponseHeader( 'Multi-Object' ) } );
        }
      ).fail(
        function( xhr )
        {
          console.error( 'Create: (' + xhr.status + '): "' + request.url + '"' );
          if( xhr.status == 500 )
          {
            this.server_error( xhr.responseText, xhr.getResponseHeader( 'Content-Type' ) );
            deferred.reject( { msg: 'Server Error' } );
          }
          else
          {
            if( xhr.responseJSON.fields )
              deferred.reject( { fields: xhr.responseJSON.fields } );
            else if( xhr.responseJSON.msg )
              deferred.reject( { msg: xhr.responseJSON.msg, code: xhr.status } );
            else
              deferred.reject( { data: xhr.responseJSON, code: xhr.status } );
          }
        }.bind( this )
      );

      return deferred.promise();
    };

    cinp.update = function( uri, values )
    {
      var deferred = $.Deferred();

      var request = this.makeRequest( 'UPDATE', uri, values );

      console.info( 'Update: "' + request.url + '"' );

      var req = $.ajax( request );

      req.done(
        function( data, status, xhr )
        {
          deferred.resolve( { detail: data, multi_object: xhr.getResponseHeader( 'Multi-Object' ) } );
        }
      ).fail(
        function( xhr )
        {
          console.error( 'Update: (' + xhr.status + '): "' + request.url + '"' );
          if( xhr.status == 500 )
          {
            this.server_error( xhr.responseText, xhr.getResponseHeader( 'Content-Type' ) );
            deferred.reject( { msg: 'Server Error' } );
          }
          else
          {
            if( xhr.responseJSON.fields )
              deferred.reject( { fields: xhr.responseJSON.fields } );
            else if( xhr.responseJSON.msg )
              deferred.reject( { msg: xhr.responseJSON.msg, code: xhr.status } );
            else
              deferred.reject( { data: xhr.responseJSON, code: xhr.status } );
          }
        }.bind( this )
      );

      return deferred.promise();
    };

    cinp.call = function( uri, values )
    {
      var deferred = $.Deferred();

      var request = this.makeRequest( 'CALL', uri, values );

      console.info( 'Call: "' + request.url + '"' );

      var req = $.ajax( request );

      req.done(
        function( data, status, xhr )
        {
          deferred.resolve( { result: data, multi_object: xhr.getResponseHeader( 'Multi-Object' ) } );
        }
      ).fail(
        function( xhr )
        {
          console.error( 'Call: (' + xhr.status + '): "' + request.url + '"' );
          if( xhr.status == 500 )
          {
            this.server_error( xhr.responseText, xhr.getResponseHeader( 'Content-Type' ) );
            deferred.reject( { msg: 'Server Error' } );
          }
          else
          {
            if( xhr.responseJSON.fields )
              deferred.reject( { fields: xhr.responseJSON.fields } );
            else if( xhr.responseJSON.msg )
              deferred.reject( { msg: xhr.responseJSON.msg, code: xhr.status } );
            else
              deferred.reject( { data: xhr.responseJSON, code: xhr.status } );
          }
        }.bind( this )
      );

      return deferred.promise();
    };

    return cinp;
  };
} )();
