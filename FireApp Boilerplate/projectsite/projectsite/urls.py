from django.contrib import admin
from django.urls import path

from fire.views import HomePageView, ChartView, PieCountbySeverity, LineCountbyMonth, MultilineIncidentTop3Country, multipleBarbySeverity
from fire import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', HomePageView.as_view(), name='home'),
    path('dashboard_chart', ChartView.as_view(), name='dashboard-chart'),
    path('chart/', PieCountbySeverity, name='chart'),
    path('multilineChart/', MultilineIncidentTop3Country, name='chart'),
    path('multiBarChart/', multipleBarbySeverity, name='chart'),
    path('stations', views.map_station, name='map-station'),
    path('', views.fire_incident_list, name='fire_incident_list'),
    path('create/', views.fire_incident_create, name='fire_incident_create'),
    path('update/<int:pk>/', views.fire_incident_update, name='fire_incident_update'),
    path('delete/<int:pk>/', views.fire_incident_delete, name='fire_incident_delete'),

]
