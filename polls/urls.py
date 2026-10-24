# polls/urls.py

from django.urls import path
from . import views

# urlpatterns = [
#     # Dashboard / Home
#     path('', views.dashboard, name='dashboard'),
    
#     # Poll Creation & Code Lookup
#     path('create/', views.create_poll, name='create_poll'),
#     path('search/', views.search_poll, name='search_poll'),
    
#     # Voting Ballot & Verification Gate
#     path('vote/<str:code>/', views.vote_ballot, name='vote_ballot'),
    
#     # Chart Analytics & Results Page
#     path('results/<str:code>/', views.poll_results, name='poll_results'),
    
#     # Creator Management View
#     path('manage/<str:code>/', views.poll_detail, name='poll_detail'),
# ]


# polls/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('create/', views.create_poll, name='create_poll'),
    path('search/', views.search_poll, name='search_poll'),
    path('vote/ballot/', views.vote_ballot, name='vote_ballot'),  # Clean URL without exposing raw codes
    path('results/<str:code>/', views.poll_results, name='poll_results'),
    path('manage/<str:code>/', views.poll_detail, name='poll_detail'),
]