from django import forms
from .models import Trip, Expense


# =========================================================
# TRIP FORM
# =========================================================

class TripForm(forms.ModelForm):

    class Meta:
        model = Trip

        fields = [
            'source',
            'destination',
            'travel_date',
            'phone_number',
            'vehicle_type',
            'total_seats',
            'filled_seats',
        ]

        widgets = {

            'source': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter starting location'
                }
            ),

            'destination': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter destination'
                }
            ),

            'travel_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),

            'phone_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter phone number'
                }
            ),

            'vehicle_type': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter vehicle type (Car, Bike, SUV...)'
                }
            ),

            'total_seats': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1',
                    'placeholder': 'Enter total seats'
                }
            ),

            'filled_seats': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0',
                    'placeholder': 'Enter filled seats'
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        total_seats = cleaned_data.get('total_seats')
        filled_seats = cleaned_data.get('filled_seats')

        if (
            total_seats is not None
            and filled_seats is not None
            and filled_seats > total_seats
        ):
            self.add_error(
                'filled_seats',
                'Filled seats cannot be greater than total seats.'
            )

        return cleaned_data


# =========================================================
# EXPENSE FORM
# =========================================================

class ExpenseForm(forms.ModelForm):

    class Meta:
        model = Expense

        fields = [
            'description',
            'paid_by',
            'amount',
            'number_of_people',
        ]

        widgets = {

            'description': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter expense description'
                }
            ),

            'paid_by': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Who paid?'
                }
            ),

            'amount': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': '0',
                    'placeholder': 'Enter amount'
                }
            ),

            'number_of_people': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1',
                    'placeholder': 'Enter number of people'
                }
            ),
        }