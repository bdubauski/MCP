

class Git():
  def __init__( self, repo ):
    self.repo = repo

  def postCommitComment( self, commit_hash, comment, line=None, path=None, position=None ):
    pass

  def postCommitStatus( self, commit_hash, state, target_url=None, description=None ):
    pass

  def postMergeComment( self, id, comment ):
    pass

  def getMergeList( self ):
    return [ ]

  def branchToMerge( self, branch_name ):
    return None

  def mergeToBranch( self, merge ):
    raise Exception( 'Merges not supported by generic git' )

  def mergeToRef( self, merge ):
    raise Exception( 'Merges not supported by generic git' )
