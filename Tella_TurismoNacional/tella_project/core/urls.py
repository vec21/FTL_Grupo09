from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('destinos/', views.destinos, name='destinos'),
    path('planejador/', views.planejador, name='planejador'),
    path('api/places/search/', views.api_places_search, name='api_places_search'),
    path('api/places/photo/<str:place_id>/<path:photo_ref>/', views.api_place_photo, name='api_place_photo'),
    path('api/places/estimate/', views.estimate_place_cost, name='estimate_place_cost'),
    path('login/', views.login_view, name='login'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('logout/', views.logout_view, name='logout'),
    path('ui/', views.ui_placeholder, name='ui'),
    path('sobre/', views.sobre, name='sobre'),
    path('contato/', views.contato, name='contato'),
]
