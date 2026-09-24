from django.urls import path

from . import views


urlpatterns = [

    # ---------------- HOME ----------------

    path(
        '',
        views.home,
        name='home'
    ),


    # ---------------- REGISTER ----------------

    path(
        'register/',
        views.register_view,
        name='register'
    ),


    # ---------------- LOGIN ----------------

    path(
        'login/',
        views.login_view,
        name='login'
    ),


    # ---------------- LOGOUT ----------------

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),


    # ---------------- DASHBOARD ----------------

    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),


    # ---------------- ADD TRIP ----------------

    path(
        'add-trip/',
        views.add_trip,
        name='add_trip'
    ),


    # ---------------- MATCHES ----------------

    path(
        'matches/',
        views.find_matches,
        name='find_matches'
    ),


    # ---------------- SEND TRIP REQUEST ----------------

    # Passenger sends request to vehicle owner

    path(
        'trip/request/<int:trip_id>/',
        views.send_trip_request,
        name='send_trip_request'
    ),


    # ---------------- ACCEPT / REJECT REQUEST ----------------

    # Vehicle owner accepts or rejects passenger

    path(
        'trip/request-action/<int:request_id>/<str:action>/',
        views.update_trip_request,
        name='update_trip_request'
    ),


    # ---------------- BUDGET ----------------

    path(
        'budget/',
        views.budget,
        name='budget'
    ),


    # ---------------- EXPENSES ----------------

    path(
        'expenses/',
        views.expenses,
        name='expenses'
    ),

]