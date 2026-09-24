from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q,F

from .models import Trip, Expense, TripRequest
from .forms import TripForm, ExpenseForm

from google import genai
from dotenv import load_dotenv
import os


# =========================================================
# GEMINI CONFIGURATION
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# =========================================================
# HOME
# =========================================================

def home(request):
    return render(
        request,
        'travel/home.html'
    )


# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                'Username already exists.'
            )

            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        login(request, user)

        return redirect('dashboard')

    return render(
        request,
        'travel/register.html'
    )


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('dashboard')

        messages.error(
            request,
            'Invalid username or password.'
        )

    return render(
        request,
        'travel/login.html'
    )


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    logout(request)

    return redirect('home')


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard(request):

    trips = Trip.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(
        request,
        'travel/dashboard.html',
        {
            'trips': trips
        }
    )


# =========================================================
# ADD TRIP
# =========================================================

@login_required
def add_trip(request):

    if request.method == 'POST':

        form = TripForm(request.POST)

        if form.is_valid():

            trip = form.save(commit=False)

            trip.user = request.user

            vehicle_type = form.cleaned_data.get(
                'vehicle_type'
            )

            total_seats = form.cleaned_data.get(
                'total_seats'
            )

            filled_seats = form.cleaned_data.get(
                'filled_seats'
            )

            # -------------------------------------------------
            # USER HAS ENTERED VEHICLE
            # -------------------------------------------------

            if vehicle_type and vehicle_type.strip():

                trip.vehicle_type = vehicle_type.strip()

                trip.total_seats = (
                    total_seats
                    if total_seats is not None
                    else 4
                )

                trip.filled_seats = (
                    filled_seats
                    if filled_seats is not None
                    else 0
                )

            # -------------------------------------------------
            # USER DOES NOT HAVE VEHICLE
            # -------------------------------------------------

            else:

                trip.vehicle_type = ''

                trip.total_seats = 0

                trip.filled_seats = 0

            trip.save()

            messages.success(
                request,
                'Trip added successfully.'
            )

            return redirect('find_matches')

    else:

        form = TripForm()

    return render(
        request,
        'travel/match.html',
        {
            'form': form
        }
    )


# =========================================================
# FIND MATCHES
# =========================================================

@login_required
def find_matches(request):

    current_trip = Trip.objects.filter(
        user=request.user
    ).order_by('-created_at').first()

    if not current_trip:

        messages.warning(
            request,
            'Please add your trip first.'
        )

        return redirect('add_trip')

    # -----------------------------------------------------
    # SAME DESTINATION + SAME DATE
    # -----------------------------------------------------

    base_matches = Trip.objects.filter(
        destination__iexact=current_trip.destination.strip(),
        travel_date=current_trip.travel_date
    ).exclude(
        user=request.user
    )

    # -----------------------------------------------------
    # CHECK CURRENT USER VEHICLE
    # -----------------------------------------------------

    current_has_vehicle = bool(
        current_trip.vehicle_type
        and current_trip.vehicle_type.strip()
    )

    # -----------------------------------------------------
    # USER HAS VEHICLE
    # SHOW PASSENGERS
    # -----------------------------------------------------

    if current_has_vehicle:

        matches = base_matches.filter(
            Q(vehicle_type__isnull=True) |
            Q(vehicle_type='')
        )

        match_type = 'passengers'

    # -----------------------------------------------------
    # USER IS PASSENGER
    # SHOW VEHICLE OWNERS
    # -----------------------------------------------------

    else:

        matches = base_matches.exclude(
            Q(vehicle_type__isnull=True) |
            Q(vehicle_type='')
        )

        # Only vehicles with available seats
        matches = matches.filter(
            filled_seats__lt=F('total_seats')
        )

        match_type = 'vehicle_owners'

    matches = matches.distinct().order_by(
        '-created_at'
    )

    return render(
        request,
        'travel/matches.html',
        {
            'trip': current_trip,
            'matches': matches,
            'match_type': match_type
        }
    )


# =========================================================
# SEND TRIP REQUEST
# =========================================================

@login_required
def send_trip_request(request, trip_id):

    vehicle_trip = get_object_or_404(
        Trip,
        id=trip_id
    )

    # -----------------------------------------------------
    # CHECK VEHICLE
    # -----------------------------------------------------

    if not vehicle_trip.vehicle_type:

        messages.error(
            request,
            'This traveller does not have a vehicle.'
        )

        return redirect('find_matches')

    # -----------------------------------------------------
    # CANNOT REQUEST YOUR OWN TRIP
    # -----------------------------------------------------

    if vehicle_trip.user == request.user:

        messages.error(
            request,
            'You cannot send a request to yourself.'
        )

        return redirect('find_matches')

    # -----------------------------------------------------
    # CURRENT USER TRIP
    # -----------------------------------------------------

    sender_trip = Trip.objects.filter(
        user=request.user
    ).order_by('-created_at').first()

    if not sender_trip:

        messages.error(
            request,
            'Please add your trip first.'
        )

        return redirect('add_trip')

    # -----------------------------------------------------
    # CURRENT USER MUST BE PASSENGER
    # -----------------------------------------------------

    if sender_trip.vehicle_type:

        messages.error(
            request,
            'Only passengers can send a request.'
        )

        return redirect('find_matches')

    # -----------------------------------------------------
    # DESTINATION CHECK
    # -----------------------------------------------------

    if (
        sender_trip.destination.strip().lower()
        != vehicle_trip.destination.strip().lower()
    ):

        messages.error(
            request,
            'Destination does not match.'
        )

        return redirect('find_matches')

    # -----------------------------------------------------
    # DATE CHECK
    # -----------------------------------------------------

    if sender_trip.travel_date != vehicle_trip.travel_date:

        messages.error(
            request,
            'Travel date does not match.'
        )

        return redirect('find_matches')

    # -----------------------------------------------------
    # AVAILABLE SEATS
    # -----------------------------------------------------

    if vehicle_trip.available_seats <= 0:

        messages.error(
            request,
            'No seats are available in this vehicle.'
        )

        return redirect('find_matches')

    # -----------------------------------------------------
    # CHECK EXISTING REQUEST
    # -----------------------------------------------------

    existing_request = TripRequest.objects.filter(
        trip=vehicle_trip,
        sender=request.user
    ).first()

    if existing_request:

        if existing_request.status == 'Pending':

            messages.warning(
                request,
                'Request already sent.'
            )

        elif existing_request.status == 'Accepted':

            messages.success(
                request,
                'Your request has already been accepted.'
            )

        elif existing_request.status == 'Rejected':

            messages.warning(
                request,
                'Your request was rejected.'
            )

        return redirect('find_matches')

    # -----------------------------------------------------
    # CREATE REQUEST
    # -----------------------------------------------------

    TripRequest.objects.create(
        trip=vehicle_trip,
        sender=request.user,
        status='Pending'
    )

    messages.success(
        request,
        'Request sent successfully.'
    )

    return redirect('find_matches')


# =========================================================
# ACCEPT / REJECT TRIP REQUEST
# =========================================================

@login_required
def update_trip_request(
    request,
    request_id,
    action
):

    trip_request = get_object_or_404(
        TripRequest,
        id=request_id
    )

    vehicle_trip = trip_request.trip

    # -----------------------------------------------------
    # ONLY VEHICLE OWNER
    # -----------------------------------------------------

    if vehicle_trip.user != request.user:

        messages.error(
            request,
            'You are not allowed to perform this action.'
        )

        return redirect('find_matches')

    # -----------------------------------------------------
    # REQUEST MUST BE PENDING
    # -----------------------------------------------------

    if trip_request.status != 'Pending':

        messages.warning(
            request,
            'This request has already been processed.'
        )

        return redirect('find_matches')

    # =====================================================
    # ACCEPT
    # =====================================================

    if action == 'accept':

        if vehicle_trip.available_seats <= 0:

            messages.error(
                request,
                'No seats are available.'
            )

            return redirect('find_matches')

        trip_request.status = 'Accepted'
        trip_request.save()

        vehicle_trip.filled_seats += 1
        vehicle_trip.save()

        messages.success(
            request,
            f'Request from '
            f'{trip_request.sender.username} '
            f'accepted.'
        )

    # =====================================================
    # REJECT
    # =====================================================

    elif action == 'reject':

        trip_request.status = 'Rejected'
        trip_request.save()

        messages.success(
            request,
            f'Request from '
            f'{trip_request.sender.username} '
            f'rejected.'
        )

    return redirect('find_matches')


# =========================================================
# BUDGET
# =========================================================

def budget(request):

    ai_result = None

    if request.method == 'POST':

        destination = request.POST.get(
            'destination'
        )

        people = request.POST.get(
            'people'
        )

        days = request.POST.get(
            'days'
        )

        if client:

            prompt = f"""
You are a smart travel budget assistant.

Destination: {destination}
Number of people: {people}
Number of days: {days}

Give a simple estimated travel budget
in Indian Rupees.

Include:

1. Transportation
2. Accommodation
3. Food
4. Local travel
5. Activities
6. Emergency amount

Also give:

- Approximate total
- Approximate amount per person
- 3 money-saving tips

This is an estimated budget before the journey.
Do not present it as an actual ticket price.

Keep the answer simple and practical.
"""

            try:

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )

                ai_result = response.text

            except Exception as e:

                ai_result = f"Gemini Error: {str(e)}"

        else:

            ai_result = (
                "Gemini API key is not configured. "
                "Please check your .env file."
            )

    return render(
        request,
        'travel/budget.html',
        {
            'ai_result': ai_result
        }
    )


# =========================================================
# EXPENSES
# =========================================================

@login_required
def expenses(request):

    trip = Trip.objects.filter(
        user=request.user
    ).order_by('-created_at').first()

    if not trip:

        return redirect('add_trip')

    # -----------------------------------------------------
    # ADD EXPENSE
    # -----------------------------------------------------

    if request.method == 'POST':

        form = ExpenseForm(request.POST)

        if form.is_valid():

            expense = form.save(commit=False)

            expense.user = request.user
            expense.trip = trip

            expense.save()

            messages.success(
                request,
                'Expense added successfully.'
            )

            return redirect('expenses')

    else:

        form = ExpenseForm()

    # -----------------------------------------------------
    # EXPENSE LIST
    # -----------------------------------------------------

    expense_list = Expense.objects.filter(
        trip=trip
    ).order_by('-created_at')

    # -----------------------------------------------------
    # TOTAL EXPENSE
    # -----------------------------------------------------

    total = expense_list.aggregate(
        total=Sum('amount')
    )['total'] or 0

    return render(
        request,
        'travel/expenses.html',
        {
            'form': form,
            'expense_list': expense_list,
            'total': total,
            'trip': trip
        }
    )