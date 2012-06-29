 # -*- coding:utf-8 -*-
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_push.publisher import ping_hub
from django.contrib.sites.models import Site
from djrdf.models import djRdf

# from rq import Queue, use_connection
# use_connection()
# q = Queue()


import django_rq
redis_conn = django_rq.get_connection('high')
q = django_rq.get_queue('high')


# Listener tool
@receiver(post_save)
def post_save_callback(sender, instance, **kwargs):
    print "Post save callback with sender %s and instance %s" % (sender, instance)
    if djRdf in sender.__mro__:
        feed_url = 'http://%s/%s/%s/' % (Site.objects.get_current(), 'feed', sender.__name__.lower())
        print "DO NO ping hub for %s " % feed_url
        # ping_hub(feed_url)
        # q.enqueue(ping_hub, feed_url)

