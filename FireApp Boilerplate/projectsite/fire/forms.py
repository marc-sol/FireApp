from django import forms
from .models import FireIncident
from django.core.exceptions import ValidationError
from datetime import datetime

class FireIncidentForm(forms.ModelForm):
    class Meta:
        model = FireIncident
        fields = ['location', 'date', 'severity', 'description']

def date(self):
        date = self.data.get('date')

        if date > datetime.now():
            raise ValidationError("Wrong Date.")

        return date

def temperature(self):
        temperature = self.data.get('temperature')
        if temperature < 0:
            raise ValidationError("Invalid Input")
        return temperature

def humidity(self):
    humidity = self.data.get('humidity')
    if humidity < 0:
        raise ValidationError("Invalid Input")
    return humidity

def wind_speed(self):
    wind_speed = self.data.get('wind_speed')
    if wind_speed < 0:
        raise ValidationError("Invalid Input")
    return wind_speed