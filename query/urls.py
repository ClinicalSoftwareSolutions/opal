from django.conf.urls import patterns, url

from query import views

urlpatterns = patterns(
    '',
    url(r'^builder.html$', views.QueryBuilderView.as_view()),
    )
