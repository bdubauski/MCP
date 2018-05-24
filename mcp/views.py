from django.shortcuts import redirect


def index( request ):
  return redirect( '/ui/' )


def oauth( requires ):
  pass  # username should be a paramater, needs to be a post
  # https://developer.github.com/v3/oauth/
