from django.urls import path
from . import views
from rest_framework.urlpatterns import format_suffix_patterns

app_name = "polls"

# Regular URL patterns
urlpatterns = [
    path('list/', views.polls_list, name='list'),
    path('list/user/', views.list_by_user, name='list_by_user'),
    path('add/', views.polls_add, name='add'),
    path('edit/<int:poll_id>/', views.polls_edit, name='edit'),
    path('delete/<int:poll_id>/', views.poll_delete, name='delete'),
    path('end/<int:poll_id>/', views.end_poll, name='end_poll'),
    path('edit/<int:poll_id>/choice/add/', views.add_choice, name='add_choice'),
    path('edit/choice/<int:choice_id>/', views.choice_edit, name='choice_edit'),
    path('delete/choice/<int:choice_id>/', views.choice_delete, name='choice_delete'),
    path('<int:poll_id>/', views.poll_detail, name='detail'),
    path('<int:poll_id>/vote/', views.vote, name='vote'),
    path('<int:poll_id>/results/', views.poll_results, name='results'),
]

# API URL patterns
api_urlpatterns = [
    path('api/polls/', views.PollViewSet.as_view({'get': 'list', 'post': 'create'}), name='poll-list'), 
    path('api/polls/<int:pk>/', views.PollViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    }), name='poll-detail'), 
    path('api/choices/', views.ChoiceViewSet.as_view({'get': 'list', 'post': 'create'}), name='choice-list'), 
    path('api/choices/<int:pk>/', views.ChoiceViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='choice-detail'), 
    path('api/choices/<int:pk>/vote/', views.ChoiceViewSet.as_view({'post': 'vote'}), name='choice-vote'), 
    path('api/votes/', views.VoteViewSet.as_view({'get': 'list', 'post': 'create'}), name='vote-list'), 
    path('api/votes/<int:pk>/', views.VoteViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='vote-detail')]

# Add API URLs to urlpatterns
urlpatterns += format_suffix_patterns(api_urlpatterns)
