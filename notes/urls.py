from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_note_view, name='create_note'),
    path('', views.list_notes, name='list_notes'),
    path('edit/<int:note_id>/', views.edit_note, name='edit_note'),
    path('delete/<int:note_id>/', views.delete_note, name='delete_note'),
    path('verify/<int:note_id>/', views.verify_receipt, name='verify_receipt'),
]