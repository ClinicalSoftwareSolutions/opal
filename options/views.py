import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse

from options import micro_test_defaults
from options.models import option_models, Synonym
from patients.models import TAGS

def _build_json_response(data, status_code=200):
    response = HttpResponse()
    response['Content-Type'] = 'application/json'
    response.content = json.dumps(data, cls=DjangoJSONEncoder)
    response.status_code = status_code
    return response

def options_view(request):
    data = {}
    for name, model in option_models.items():
        options = [instance.name for instance in model.objects.all()]
        data[name] = options

    for synonym in Synonym.objects.all():
        name = type(synonym.content_object).__name__.lower()
        data[name].append(synonym.name)

    for name in data:
        data[name].sort()

    data['micro_test_defaults'] = micro_test_defaults

    tag_hierarchy = {}
    tag_display = {}
    for tag in TAGS:
        tag_display[tag.name] = tag.title
        if tag.subtags:
            tag_hierarchy[tag.name] = [st.name for st in tag.subtags]
            for t in tag.subtags:
                tag_display[t.name] = t.title
        else:
            tag_hierarchy[tag.name] = []
    data['tag_hierarchy'] = tag_hierarchy
    data['tag_display'] = tag_display

    return _build_json_response(data)
