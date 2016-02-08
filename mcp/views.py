from django.shortcuts import render
from django.template import Template, Context
from django.conf import settings

from mcp.Project.models import Project, Commit
from mcp.Processor.models import QueueItem, BuildJob, Promotion
from plato.Config.models import Config

def index( request ):
    c = Context( {} )
    return render(request, 'index.html', c)

def projects( request ):
    c = Context( {
                    'job_list': BuildJob.objects.all().order_by( 'pk' ),
                    'queue_list': QueueItem.objects.all().order_by( '-priority' ),
                    'promotion_list': Promotion.objects.all().order_by( 'pk' ),
                    'project_list': Project.objects.all().order_by( 'pk' ),
                    'commit_list': Commit.objects.filter( done_at__isnull=True ).order_by( 'pk' ),
                    'unused_list': Config.objects.filter( profile=settings.HARDWARE_PROFILE, configured__isnull=True ).order_by( 'pk' )
                  } )
    return render(request, 'projects.html', c)
