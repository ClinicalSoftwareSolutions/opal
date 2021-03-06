import json
import datetime

from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods
from django.template.loader import select_template
from django.utils.decorators import method_decorator
from django.utils import formats
from django.contrib.auth.decorators import login_required

from utils.http import with_no_caching
from utils import camelcase_to_underscore
from patients import models, schema, exceptions

class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)

@require_http_methods(['GET'])
def patient_detail_view(request, pk):
    try:
        patient = models.Patient.objects.get(pk=pk)
    except models.Patient.DoesNotExist:
        return HttpResponseNotFound()

    return _build_json_response(patient.to_dict(), 200)

@with_no_caching
@require_http_methods(['GET', 'POST'])
def patient_list_and_create_view(request):
    if request.method == 'GET':
        GET = request.GET

        search_terms = {}
        filter_dict = {}

        if 'hospital_number' in GET:
            search_terms['hospital_number'] = GET['hospital_number']
            filter_dict['demographics__hospital_number__iexact'] = GET['hospital_number']

        if 'name' in GET:
            search_terms['name'] = GET['name']
            filter_dict['demographics__name__icontains'] = GET['name']

        if filter_dict:
            patients = models.Patient.objects.filter(**filter_dict).order_by('demographics__date_of_birth')
        else:
            patients = models.Patient.objects.all().order_by('demographics__date_of_birth')

        return _build_json_response([patient.to_dict() for patient in patients])

    elif request.method == 'POST':
        data = _get_request_data(request)
        hospital_number = data['demographics'].get('hospital_number', '')
        if hospital_number:
            try:
                patient = models.Patient.objects.get(demographics__hospital_number=hospital_number)
            except models.Patient.DoesNotExist:
                patient = models.Patient.objects.create()
        else:
            patient = models.Patient.objects.create()

        patient.update_from_dict(data, request.user)
        return _build_json_response(patient.to_dict(), 201)

@require_http_methods(['GET', 'PUT', 'DELETE'])
def subrecord_detail_view(request, model, pk):
    try:
        subrecord = model.objects.get(pk=pk)
    except model.DoesNotExist:
        return HttpResponseNotFound()

    if request.method == 'GET':
        return _build_json_response(subrecord.to_dict())
    elif request.method == 'PUT':
        data = _get_request_data(request)
        try:
            subrecord.update_from_dict(data, request.user)
            return _build_json_response(subrecord.to_dict())
        except exceptions.ConsistencyError:
            return _build_json_response({'error': 'Item has changed'}, 409)
    elif request.method == 'DELETE':
        subrecord.delete()
        return _build_json_response('')

@require_http_methods(['POST'])
def subrecord_create_view(request, model):
    subrecord = model()
    data = _get_request_data(request)
    subrecord.update_from_dict(data, request.user)
    return _build_json_response(subrecord.to_dict(), 201)

def _get_request_data(request):
    data = request.read()
    return json.loads(data)

def _build_json_response(data, status_code=200):
    response = HttpResponse()
    response['Content-Type'] = 'application/json'
    response.content = json.dumps(data, cls=DjangoJSONEncoder)
    response.status_code = status_code
    return response


class PatientTemplateView(TemplateView):
    def get_column_context(self):
        """
        Return the context for our columns
        """
        context = []
        for column in self.column_schema:
            column_context = {}
            name = camelcase_to_underscore(column.__name__)
            column_context['name'] = name
            column_context['title'] = getattr(column, '_title',
                                              name.replace('_', ' ').title())
            column_context['single'] = column._is_singleton
            column_context['template_path'] = name + '.html'
            column_context['modal_template_path'] = name + '_modal.html'
            column_context['detail_template_path'] = select_template([name + '_detail.html', name + '.html']).name
            context.append(column_context)
        return context

    def get_context_data(self, **kwargs):
        context = super(PatientTemplateView, self).get_context_data(**kwargs)
        context['tags'] = models.TAGS
        context['columns'] = self.get_column_context()
        return context


class PatientListTemplateView(PatientTemplateView):
    template_name = 'patient_list.html'
    column_schema = schema.list_columns

class PatientDetailTemplateView(PatientTemplateView):
    template_name = 'patient_detail.html'
    column_schema = schema.detail_columns

class SearchTemplateView(TemplateView):
    template_name = 'search.html'

    def get_context_data(self, **kwargs):
        context = super(SearchTemplateView, self).get_context_data(**kwargs)
        context['tags'] = models.TAGS
        return context

class AddPatientTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'add_patient_modal.html'

    def get_context_data(self, **kwargs):
        context = super(AddPatientTemplateView, self).get_context_data(**kwargs)
        context['tags'] = models.TAGS
        return context

class DischargePatientTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'discharge_patient_modal.html'

class DeleteItemConfirmationView(LoginRequiredMixin, TemplateView):
    template_name = 'delete_item_confirmation_modal.html'

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = 'opal.html'

class ModalTemplateView(LoginRequiredMixin, TemplateView):
    template_name = 'modal_base.html'

    def get_context_data(self, **kwargs):
        context = super(ModalTemplateView, self).get_context_data(**kwargs)
        column = self.kwargs['model']
        name = camelcase_to_underscore(column.__name__)

        context['name'] = name
        context['title'] = getattr(column, '_title', name.replace('_', ' ').title())
        context['single'] = column._is_singleton
        context['modal_template_path'] = name + '_modal.html'

        if name == 'location':
            context['tags'] = models.TAGS

        return context

# This probably doesn't belong here
class ContactView(TemplateView):
    template_name = 'contact.html'

def list_schema_view(request):
    columns = []
    for column in schema.list_columns:
        columns.append({
            'name': column.get_api_name(),
            'single': column._is_singleton,
            'fields': column.build_field_schema()
        })

    return _build_json_response(columns)

def detail_schema_view(request):
    columns = []
    for column in schema.detail_columns:
        columns.append({
            'name': column.get_api_name(),
            'single': column._is_singleton,
            'fields': column.build_field_schema()
        })

    return _build_json_response(columns)
