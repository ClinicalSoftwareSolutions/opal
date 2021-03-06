from django.conf.urls import patterns, url
from utils import camelcase_to_underscore
from patients import models, views

urlpatterns = patterns('',
    url(r'^patient_list.html/?$', views.PatientListTemplateView.as_view()),
    url(r'^patient_detail.html/?$', views.PatientDetailTemplateView.as_view()),
    url(r'^search.html/?$', views.SearchTemplateView.as_view()),
    url(r'^modals/add_patient.html/?$', views.AddPatientTemplateView.as_view()),
    url(r'^modals/discharge_patient.html/?$', views.DischargePatientTemplateView.as_view()),
    url(r'^modals/delete_item_confirmation.html/?$', views.DeleteItemConfirmationView.as_view()),
)

for subrecord_model in models.Subrecord.__subclasses__():
    sub_url = camelcase_to_underscore(subrecord_model.__name__)
    urlpatterns += patterns('',
        url(r'^modals/%s.html/?$' % sub_url, views.ModalTemplateView.as_view(), {'model': subrecord_model}),
    )
