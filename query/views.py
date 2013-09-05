"""
Urls for an OPAL querybuilder interface
"""
from django.views.generic import TemplateView

class QueryBuilderView(TemplateView):
    template_name = 'query/builder.html'
