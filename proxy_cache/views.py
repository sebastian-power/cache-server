from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
import redis
import httpx
from django.conf import settings
from .tasks import cache_response

import json

UPSTREAM_BASE = "https://dummyjson.com"
CACHE_PREFIX = getattr(settings, "CACHE_PREFIX")

@api_view(["GET"])
def proxy(request, subpath=""):
	rds_key = CACHE_PREFIX + subpath
	rds = redis.Redis(host="localhost", port=6379, decode_responses=True)
	if rds.exists(CACHE_PREFIX+subpath):
		return Response(json.loads(rds.get(rds_key)), headers={"X-Cache": "HIT"})
	upstream_url = f"{UPSTREAM_BASE}/{subpath}"
	resp = httpx.get(upstream_url)
	resp.raise_for_status()
	payload = resp.json()
	cache_response.delay(subpath, payload)
	return Response(payload, headers={"X-Cache": "MISS"})
