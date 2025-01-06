from django.contrib import admin

from .models import Incident, Locations, Firefighters, FireStation, FireTruck, WeatherConditions

@admin.register(FireTruck)
class FireTruck(admin.ModelAdmin):
    list_display = ("truck_number", "model","capacity", "station")
    search_fields = ("truck_number", "model","capacity")

@admin.register(Firefighters)
class FfightersAdmin(admin.ModelAdmin):
    list_display = ("name", "rank","experience_level", "station")
    search_fields = ("name", "rank","experience_level")

@admin.register(Locations)
class LocationsAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude","longitude", "address", "city","country")
    search_fields = ("name", "address","city","country")

@admin.register(FireStation)
class FstationAdmin(admin.ModelAdmin):
    list_display = ("name", "latitude","longitude", "address", "city","country")
    search_fields = ("name", "address","city","country")


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("location", "date_time","severity_level", "description")
    search_fields = ("location__name", "date_time","severity_level")

@admin.register(WeatherConditions)
class WConditionsAdmin(admin.ModelAdmin):
    list_display = ("incident", "temperature","humidity", "wind_speed","weather_description")
    search_fields = ("incident__location__name","humidity","wind_speed","weather_description")