from django.contrib import admin

class MCPModelAdmin( admin.ModelAdmin ):
  def save_model( self, request, obj, form, change ):
      # Tell Django to save objects to the 'other' database.
      obj.save( using='mcp' )

  def delete_model( self, request, obj ):
      # Tell Django to delete objects from the 'other' database
      obj.delete( using='mcp' )

  def queryset( self, request ):
      # Tell Django to look for objects on the 'other' database.
      return super( MCPModelAdmin, self ).queryset( request ).using( 'mcp' )

  def formfield_for_foreignkey( self, db_field, request=None, **kwargs ):
      # Tell Django to populate ForeignKey widgets using a query
      # on the 'other' database.
      return super( MCPModelAdmin, self).formfield_for_foreignkey( db_field, request=request, using='mcp', **kwargs )

  def formfield_for_manytomany( self, db_field, request=None, **kwargs ):
      # Tell Django to populate ManyToMany widgets using a query
      # on the 'other' database.
      return super( MCPModelAdmin, self).formfield_for_manytomany( db_field, request=request, using='mcp', **kwargs )
