from celery import shared_task
from redis import Redis
from django.conf import settings
import json

CACHE_PREFIX = getattr(settings, "CACHE_PREFIX")

@shared_task
def cache_response(subpath, payload):
	rds = Redis(decode_responses=True, db=1)
	rds.set(CACHE_PREFIX + subpath, json.dumps(payload))
