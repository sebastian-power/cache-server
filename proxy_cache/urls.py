from django.urls import path
from .views import proxy

urlpatterns = [
	path("<path:subpath>", proxy),
	path('', proxy)
]
