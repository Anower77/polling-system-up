from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Avg
from polls.models import Poll, Vote
from quiz.models import Quiz, QuizAttempt

@login_required
def dashboard(request):
    # Get user-specific stats
    context = {
        'user_polls_count': Poll.objects.filter(owner=request.user).count(),
        'user_quizzes_count': Quiz.objects.filter(creator=request.user).count(),
        'user_votes_count': Vote.objects.filter(user=request.user).count(),
        'quiz_score_avg': QuizAttempt.objects.filter(
            user=request.user
        ).aggregate(Avg('score'))['score__avg'] or 0,
        
        # Get recent activities
        'recent_polls': Poll.objects.filter(owner=request.user).order_by('-pub_date')[:5],
        'recent_quizzes': Quiz.objects.filter(creator=request.user).order_by('-created_at')[:5],
        'recent_votes': Vote.objects.filter(user=request.user).order_by('-vote_date')[:5],
        'recent_attempts': QuizAttempt.objects.filter(user=request.user).order_by('-completed_at')[:5],
    }
    
    return render(request, 'dashboard/dashboard.html', context)
