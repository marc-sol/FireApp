from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from fire.models import Locations, Incident, FireStation, Firefighters, FireTruck, WeatherConditions
from fire.forms import FireStationForm, FireFighterForm, FireTruckForm, LocationForm, WeatherConditionForm, IncidentForm
from django.db import connection
from django.http import JsonResponse
from django.db.models.functions import ExtractMonth
from django.urls import reverse_lazy
from django.contrib import messages

from django.db.models import Count
from datetime import datetime

from typing import Any
from django.db.models.query import QuerySet
from django.db.models import Q

class HomePageView(ListView):
    model = Locations
    context_object_name = 'home'
    template_name = "home.html"

class ChartView(ListView):
    template_name = 'chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_queryset(self, *args, **kwargs):
        pass

def PieCountbySeverity(request): 
    query = '''SELECT severity_level, COUNT(*) as count FROM fire_incident GROUP BY severity_level;''' 
    data = {}
    with connection.cursor() as cursor: 
        cursor.execute(query)
        rows = cursor.fetchall()
    
    if rows: 
        # Construct the dictionary with severity level as keys and count as values 
        data = {severity: count for severity, count in rows}
    else:
        data = {}
    return JsonResponse(data)

def LineCountbyMonth(request):
    current_year = datetime.now().year
    result = {month: 0 for month in range(1, 13)}
    incidents_per_month = Incident.objects.filter(date_time__year=current_year) \
        .values_list('date_time', flat=True)

    # Counting the number of incidents per month
    for date_time in incidents_per_month:
        month = date_time.month
        result[month] += 1
        
    # If you want to convert month numbers to month names, you can use a dictionary mapping
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
    
    result_with_month_names = {
        month_names[int(month)]: count for month, count in result.items()}
    
    return JsonResponse(result_with_month_names)

def MultilineIncidentTop3Country(request):
    query ='''
    SELECT fl.country,strftime('%m', fi.date_time) AS month,COUNT(fi.id) AS incident_count 
    FROM fire_incident fi 
    JOIN fire_locations fl ON fi.location_id = fl.id WHERE fl.country 
    IN (SELECT fl_top.country FROM fire_incident fi_top 
        JOIN fire_locations fl_top ON fi_top.location_id = fl_top.id 
        WHERE strftime('%Y', fi_top.date_time) = strftime('%Y', 'now') 
        GROUP BY fl_top.country 
        ORDER BY COUNT(fi_top.id) DESC LIMIT 3 ) 
        AND strftime('%Y', fi.date_time) = strftime('%Y', 'now') 
        GROUP BY fl.country, month 
        ORDER BY fl.country, month; '''
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        
    # Initialize a dictionary to store the result
    result = {}
    
    # Initialize a set of months from January to December
    months = set(str(i).zfill(2) for i in range(1, 13))

    # Loop through the query results
    for row in rows:
        country = row[0]
        month = row[1]
        total_incidents = row[2]
        # If the country is not in the result dictionary initialize it with all months set to zero
        if country not in result:
            result[country] = {month: 0 for month in months}
            
            # Update the incident count for the corresponding month
        result[country][month] = total_incidents

    # Ensure there are always 3 countries in the result
    while len(result) < 3:
    # Placeholder name for missing countries
        missing_country = f"Country {len(result) + 1}"
        result[missing_country] = {month: 0 for month in months}

    for country in result:
        result[country] = dict(sorted(result[country].items()))
        
    return JsonResponse(result)

def multipleBarbySeverity(request):
    query = '''
    SELECT fi.severity_level, strftime('%m', fi.date_time) AS month, COUNT(fi.id) AS incident_count
    FROM fire_incident fi
    GROUP BY fi.severity_level, month
    '''
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    
    result = {}
    months = set(str(i).zfill(2) for i in range(1, 13))
    
    for row in rows:
        level = str(row[0]) # Ensure the severity level is a string
        month = row[1]
        total_incidents = row[2]
        
        if level not in result:
            result[level] = {month: 0 for month in months}
            
        result[level][month] = total_incidents
        
    # Sort months within each severity level
    for level in result:
        result[level] = dict(sorted(result[level].items()))
    
    return JsonResponse(result)

def map_station(request):
    # Retrieve fire station data from the database
    fireStations = FireStation.objects.values('name', 'latitude', 'longitude')

    # Convert latitude and longitude to float for proper handling in JavaScript
    for fs in fireStations:
        fs['latitude'] = float(fs['latitude'])
        fs['longitude'] = float(fs['longitude'])

    # Convert QuerySet to a list
    fireStations_list = list(fireStations)

    # Prepare context to pass to the template
    context = {
        'fireStations': fireStations_list,
    }

    # Render the template with the fire station data
    return render(request, 'map_station.html', context)

def map_incident(request):
    # Retrieve incident data from the database
    incidents = Locations.objects.values('name', 'latitude', 'longitude')
    # Convert latitude and longitude to float for proper handling in JavaScript

    for fs in incidents:
        fs['latitude'] = float(fs['latitude'])
        fs['longitude'] = float(fs['longitude'])

    # Convert QuerySet to a list
    incident_list = list(incidents)
    
    # Prepare context to pass to the template
    context = {
        'incident': incident_list,
    }

    # Render the template with the incident data
    return render(request, 'map_incidents.html', context)

class FireStationList(ListView):
    model = FireStation
    content_object_name = 'fireStation'
    template_name = 'fireStation_list.html'
    paginate_by = 5

    def get_queryset(self, *args, **kwargs):
        qs = super(FireStationList, self).get_queryset(*args, **kwargs)
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q')
            qs = qs.filter(Q(name__icontains=query))
        return qs

class FireStationCreateView(CreateView):
    model = FireStation
    form_class = FireStationForm
    template_name = 'firestation_add.html'
    success_url = reverse_lazy('fireStation-list')

    def form_valid(self, form):
        name_fireStation = form.instance.name
        messages.success(self.request, f"{name_fireStation} has been added successfully.")
        return super().form_valid(form)

class FireStationUpdateView(UpdateView):
    model = FireStation
    fields = "__all__"
    context_object_name = "fireStation"
    template_name = 'firestation_edit.html'
    success_url = reverse_lazy('fireStation-list')

    def form_valid(self, form):
        fireStation_name = form.instance.name
        messages.success(self.request,f'{fireStation_name} has been Updated.')

        return super().form_valid(form)

class FireStationDeleteView(DeleteView):
    model = FireStation
    #form_class = CollegeForm
    template_name = 'firestation_del.html'
    success_url = reverse_lazy('fireStation-list')

    def form_valid(self, form):
        messages.success(self.request, f"Fire Station Deleted successfully.")
        return super().form_valid(form)

class FireFighterList(ListView):
    model = Firefighters
    content_object_name = 'fireFighter'
    template_name = 'firefighter_list.html'
    paginate_by = 5

    def get_queryset(self, *args, **kwargs):
        qs = super(FireFighterList, self).get_queryset(*args, **kwargs)
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q')
            qs = qs.filter(Q(name__icontains=query)|Q(rank__icontains=query)|
                           Q(experience_level__icontains=query)|Q(station__icontains=query))
        return qs

class FireFighterCreateView(CreateView):
    model = Firefighters
    form_class = FireFighterForm
    template_name = 'firefighter_add.html'
    success_url = reverse_lazy('fireFighter-list')

    def form_valid(self, form):
        name_fireFighter = form.instance.name
        messages.success(self.request, f"{name_fireFighter} has been added successfully.")
        return super().form_valid(form)

class FireFighterUpdateView(UpdateView):
    model = Firefighters
    fields = "__all__"
    context_object_name = "fireFighter"
    template_name = 'firefighter_edit.html'
    success_url = reverse_lazy('fireFighter-list')

    def form_valid(self, form):
        fireFighter_name = form.instance.name
        messages.success(self.request,f'{fireFighter_name} has been Updated.')

        return super().form_valid(form)

class FireFighterDeleteView(DeleteView):
    model = Firefighters
    #form_class = CollegeForm
    template_name = 'firefighter_del.html'
    success_url = reverse_lazy('fireFighter-list')

    def form_valid(self, form):
        messages.success(self.request, f"Fire Fighter Deleted successfully.")
        return super().form_valid(form)

class FireTruckList(ListView):
    model = FireTruck
    content_object_name = 'fireTruck'
    template_name = 'firetruck_list.html'
    paginate_by = 5

    def get_queryset(self, *args, **kwargs):
        qs = super(FireTruckList, self).get_queryset(*args, **kwargs)
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q')
            qs = qs.filter(Q(model__icontains=query)| Q(truck_number__icontains=query)|
                           Q(station__name__icontains=query)|Q(capacity__icontains=query))
        return qs

class FireTruckCreateView(CreateView):
    model = FireTruck
    form_class = FireTruckForm
    template_name = 'firetruck_add.html'
    success_url = reverse_lazy('fireTruck-list')

    def form_valid(self, form):
        name_fireTruck = form.instance.model
        messages.success(self.request, f"{name_fireTruck} has been added successfully.")
        return super().form_valid(form)

class FireTruckUpdateView(UpdateView):
    model = FireTruck
    fields = "__all__"
    context_object_name = "fireTruck"
    template_name = 'firetruck_edit.html'
    success_url = reverse_lazy('fireTruck-list')

    def form_valid(self, form):
        name_fireTruck = form.instance.model
        messages.success(self.request,f'{name_fireTruck} has been Updated.')

        return super().form_valid(form)

class FireTruckDeleteView(DeleteView):
    model = Firefighters
    #form_class = CollegeForm
    template_name = 'firetruck_del.html'
    success_url = reverse_lazy('fireTruck-list')

    def form_valid(self, form):
        messages.success(self.request, f"Fire Truck Deleted successfully.")
        return super().form_valid(form)
    
class LocationList(ListView):
    model = Locations
    content_object_name = 'location'
    template_name = 'location_list.html'
    paginate_by = 5

    def get_queryset(self, *args, **kwargs):
        qs = super(LocationList, self).get_queryset(*args, **kwargs)
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q')
            qs = qs.filter(Q(name__icontains=query)|Q(address__icontains=query)|
                           Q(city__icontains=query)|Q(country__icontains=query)|
                           Q(latitude__icontains=query)|Q(longitude__icontains=query))
        return qs

class LocationCreateView(CreateView):
    model = Locations
    form_class = LocationForm
    template_name = 'location_add.html'
    success_url = reverse_lazy('location-list')

    def form_valid(self, form):
        name_location = form.instance.name
        messages.success(self.request, f"{name_location} has been added successfully.")
        return super().form_valid(form)

class LocationUpdateView(UpdateView):
    model = Locations
    fields = "__all__"
    context_object_name = "location"
    template_name = 'location_edit.html'
    success_url = reverse_lazy('location-list')

    def form_valid(self, form):
        name_location = form.instance.name
        messages.success(self.request,f'{name_location} has been Updated.')

        return super().form_valid(form)

class LocationDeleteView(DeleteView):
    model = Locations
    #form_class = CollegeForm
    template_name = 'location_del.html'
    success_url = reverse_lazy('location-list')

    def form_valid(self, form):
        messages.success(self.request, f"Location Deleted successfully.")
        return super().form_valid(form)

class WeatherConditionList(ListView):
    model = WeatherConditions
    content_object_name = 'weatherCondition'
    template_name = 'weatherCondition_list.html'
    paginate_by = 5

    def get_queryset(self, *args, **kwargs):
        qs = super(WeatherConditionList, self).get_queryset(*args, **kwargs)
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q')
            qs = qs.filter(Q(weather_description__icontains=query)|Q(incident__location__name__icontains=query)|
                           Q(temperature__icontains=query)|Q(humidity__icontains=query)|
                           Q(wind_speed__icontains=query))
        return qs

class WeatherConditionCreateView(CreateView):
    model = WeatherConditions
    form_class = WeatherConditionForm
    template_name = 'weatherCondition_add.html'
    success_url = reverse_lazy('weatherCondition-list')

    def form_valid(self, form):
        name_incident = form.instance.incident
        messages.success(self.request, f"{name_incident} has been added successfully.")
        return super().form_valid(form)
    
class WeatherConditionUpdateView(UpdateView):
    model = WeatherConditions
    fields = "__all__"
    context_object_name = "weatherCondition"
    template_name = 'weatherCondition_edit.html'
    success_url = reverse_lazy('weatherCondition-list')

    def form_valid(self, form):
        name_incident = form.instance.incident
        messages.success(self.request,f'{name_incident} has been Updated.')
        return super().form_valid(form)

class WeatherConditionDeleteView(DeleteView):
    model = WeatherConditions
    #form_class = CollegeForm
    template_name = 'weatherCondition_del.html'
    success_url = reverse_lazy('weatherCondition-list')
    

    def form_valid(self, form):
        messages.success(self.request, f"Weather Deleted successfully.")
        return super().form_valid(form)

class IncidentList(ListView):
    model = Incident
    content_object_name = 'incident'
    template_name = 'incident_list.html'
    paginate_by = 5

    def get_queryset(self, *args, **kwargs):
        qs = super(IncidentList, self).get_queryset(*args, **kwargs)
        if self.request.GET.get("q") != None:
            query = self.request.GET.get('q')
            qs = qs.filter(Q(location__name__icontains=query)|Q(severity_level__icontains=query)|
                           Q(date_time__icontains=query)| Q(description__icontains=query))
        return qs

class IncidentCreateView(CreateView):
    model = Incident
    form_class = IncidentForm
    template_name = 'incident_add.html'
    success_url = reverse_lazy('incident-list')

    def form_valid(self, form):
        name_location = form.instance.location
        messages.success(self.request, f"{name_location} has been added successfully.")
        return super().form_valid(form)

class IncidentUpdateView(UpdateView):
    model = Incident
    fields = "__all__"
    context_object_name = "location"
    template_name = 'incident_edit.html'
    success_url = reverse_lazy('incident-list')

    def form_valid(self, form):
        name_location = form.instance.location.name
        messages.success(self.request,f'{name_location} has been Updated.')

        return super().form_valid(form)

class IncidentDeleteView(DeleteView):
    model = Incident
    #form_class = CollegeForm
    template_name = 'incident_del.html'
    success_url = reverse_lazy('incident-list')

    def form_valid(self, form):
        messages.success(self.request, f"Incident Deleted successfully.")
        return super().form_valid(form)