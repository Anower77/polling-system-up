from django.urls import path, include
from rest_framework_nested import routers
from . import views

app_name = 'quiz'

router = routers.DefaultRouter()
router.register(r'quizzes', views.QuizViewSet)

# Nested router for questions
questions_router = routers.NestedDefaultRouter(router, r'quizzes', lookup='quiz')
questions_router.register(r'questions', views.QuestionViewSet, basename='quiz-questions')

urlpatterns = [
    # Template views
    path('', views.quiz_list, name='list'),
    path('add/', views.add_quiz, name='add'),
    path('<int:quiz_id>/edit/', views.edit_quiz, name='edit'),
    path('<int:quiz_id>/delete/', views.quiz_delete, name='delete'),
    path('<int:quiz_id>/take/', views.take_quiz, name='take'),
    path('<int:quiz_id>/submit/', views.submit_quiz, name='submit'),
    path('results/<int:attempt_id>/', views.quiz_results, name='results'),
    path('stats/<int:quiz_id>/', views.quiz_stats, name='stats'),
    
    # Question management
    path('<int:quiz_id>/questions/add/', views.add_question, name='add_question'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/', include(questions_router.urls)),
]
