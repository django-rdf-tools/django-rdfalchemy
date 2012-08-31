 # -*- coding:utf-8 -*-
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.sites.models import Site
from django.conf import settings
from djrdf.models import djRdf
import logging
import subhub

log = logging.getLogger('djrdf')



from redis import Redis
from rq import Queue, use_connection, get_current_connection
if not get_current_connection():
    conn = Redis('127.0.0.1', settings.REDIS_PORT)
    use_connection(conn)
if not get_current_connection():
    log.error(u'Unable to create redis connection')
# use the 'default' queue
q = Queue()


# Workaround for rqworker limitation
def letsCallDistributionTaskProcess():
    log.debug(u'IN QUEUE try to  know the numbers of tasks %s' %
        len(subhub.models.DistributionTask.objects.all()))
    subhub.models.DistributionTask.objects.process(log=log)


# Listener tool
@receiver(post_save)
def post_save_callback(sender, instance, **kwargs):
    log.debug("Post save callback with sender %s and instance %s" % (sender, instance))
    if isinstance(instance, djRdf):
        log.debug(u"Publish feeds for instance  %s " % instance)
        site = Site.objects.get_current()
        model = sender.__name__.lower()
        feed_url = 'http://%s/feed/%s/' % (site, model)
        feed_url_obj = '%s%s/' % (feed_url, instance.uuid)
        subhub.publish([feed_url, feed_url_obj], instance.uri, False)
    elif isinstance(instance, subhub.models.DistributionTask) and settings.SUBHUB_MAINTENANCE_AUTO:
        try:
            log.debug("before call ENQUEUE, tasks %s" % len(subhub.models.DistributionTask.objects.all()))
            q.enqueue(letsCallDistributionTaskProcess)
            log.debug('after call ENQUEUE')
        except Exception, e:
            log.warning(u"%s" % e)
    elif isinstance(instance, subhub.models.SubscriptionTask) and settings.SUBHUB_MAINTENANCE_AUTO:
        # call the maintenance
            try:
                log.info(u'Processing verification queue...')
                subhub.models.SubscriptionTask.objects.process(log=log)
            except subhub.utils.LockError, e:
                log.warning(u"%s" % e)
    else:
        pass

