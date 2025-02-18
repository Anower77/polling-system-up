from django.contrib import admin
from .models import Quiz, Question, QuizAttempt, Answer

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'correct_answer', 'order']
    list_filter = ['quiz']
    search_fields = ['text', 'quiz__title']
    ordering = ['quiz', 'order']

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'created_at', 'is_active', 'time_limit']
    list_filter = ['is_active', 'creator']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'score', 'started_at', 'completed_at', 'is_completed']
    list_filter = ['is_completed', 'quiz']
    search_fields = ['user__username', 'quiz__title']
    date_hierarchy = 'started_at'

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'selected_answer', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['attempt__user__username', 'question__text']
