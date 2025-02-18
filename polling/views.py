from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from polls.models import Poll, Vote
from quiz.models import Quiz, QuizAttempt
from django.db.models import Count, Avg, Prefetch

def home(request):
    # Get polls with their choices and vote counts
    recent_polls = Poll.objects.annotate(
        vote_count=Count('vote')
    ).prefetch_related(
        'choice_set'
    ).order_by('-pub_date')[:5]

    context = {
        # General stats
        'total_polls': Poll.objects.count(),
        'total_votes': Vote.objects.count(),
        'total_users': User.objects.count(),
        
        # Recent activity with vote counts
        'recent_polls': recent_polls,
        'recent_quizzes': Quiz.objects.order_by('-created_at')[:5],
    }
    
    if request.user.is_authenticated:
        # Add user-specific stats
        context.update({
            'user_polls_count': Poll.objects.filter(owner=request.user).count(),
            'user_quizzes_count': Quiz.objects.filter(creator=request.user).count(),
            'user_votes_count': Vote.objects.filter(user=request.user).count(),
            'quiz_score_avg': QuizAttempt.objects.filter(
                user=request.user, 
                is_completed=True
            ).aggregate(Avg('score'))['score__avg'] or 0,
            'user_votes': Vote.objects.filter(user=request.user),
        })
    
    return render(request, 'home.html', context)

def handler404(request, exception):
    return render(request, '404.html', status=404)

def handler500(request):
    return render(request, '500.html', status=500)

def handler403(request, exception):
    return render(request, '403.html', status=403)

def handler400(request, exception):
    return render(request, '400.html', status=400) 