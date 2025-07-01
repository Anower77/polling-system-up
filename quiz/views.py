from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Avg, Count, Q, Case, When, IntegerField
from .models import Quiz, Question, QuizAttempt, Answer
from .serializers import (
    QuizSerializer, QuestionSerializer,
    QuizAttemptSerializer, QuizSubmissionSerializer
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from .forms import QuizForm, QuestionForm

class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        quiz = self.get_object()
        
        # Check if there's an incomplete attempt
        existing_attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user,
            is_completed=False
        ).first()
        
        if existing_attempt:
            serializer = QuizAttemptSerializer(existing_attempt)
            return Response(serializer.data)
        
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user
        )
        
        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        quiz = self.get_object()
        attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user,
            is_completed=False
        ).first()
        
        if not attempt:
            return Response(
                {"error": "No active attempt found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = QuizSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            answers_data = serializer.validated_data['answers']
            
            # Process answers
            total_points = 0
            max_points = 0
            
            for answer_data in answers_data:
                question = Question.objects.get(id=answer_data['question'])
                max_points += question.points
                
                answer = Answer.objects.create(
                    attempt=attempt,
                    question=question,
                    selected_choice=answer_data['choice']
                )
                
                if answer.is_correct:
                    total_points += question.points
            
            # Calculate score as percentage
            score = (total_points / max_points) * 100 if max_points > 0 else 0
            
            # Update attempt
            attempt.score = score
            attempt.completed_at = timezone.now()
            attempt.is_completed = True
            attempt.save()
            
            return Response({
                "score": score,
                "passing_score": quiz.passing_score,
                "passed": score >= quiz.passing_score
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def statistics(self, request, pk=None):
        quiz = self.get_object()
        attempts = QuizAttempt.objects.filter(quiz=quiz, is_completed=True)
        
        stats = {
            "total_attempts": attempts.count(),
            "average_score": attempts.aggregate(Avg('score'))['score__avg'],
            "pass_rate": attempts.filter(
                score__gte=quiz.passing_score
            ).count() / attempts.count() * 100 if attempts.exists() else 0,
        }
        
        return Response(stats)

class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        quiz_id = self.kwargs.get('quiz_pk')
        if quiz_id:
            return Question.objects.filter(quiz_id=quiz_id)
        return Question.objects.all()

    def perform_create(self, serializer):
        quiz_id = self.kwargs.get('quiz_pk')
        if quiz_id:
            quiz = get_object_or_404(Quiz, pk=quiz_id)
            if quiz.creator != self.request.user:
                raise permissions.PermissionDenied()
            serializer.save(quiz=quiz)
        else:
            serializer.save()

@login_required
def quiz_list(request):
    quizzes = Quiz.objects.all()
    search_term = request.GET.get('search', '')
    filter_type = request.GET.get('filter', '')
    
    # Filter by search term if provided
    if search_term:
        quizzes = quizzes.filter(
            Q(title__icontains=search_term) |
            Q(creator__username__icontains=search_term) |
            Q(description__icontains=search_term)
        )
    
    # Apply filters
    if filter_type == 'my':
        quizzes = quizzes.filter(creator=request.user)
    elif filter_type == 'attempted':
        attempted_quiz_ids = QuizAttempt.objects.filter(
            user=request.user
        ).values_list('quiz_id', flat=True)
        quizzes = quizzes.filter(id__in=attempted_quiz_ids)
    elif filter_type == 'not-attempted':
        attempted_quiz_ids = QuizAttempt.objects.filter(
            user=request.user
        ).values_list('quiz_id', flat=True)
        quizzes = quizzes.exclude(id__in=attempted_quiz_ids)
    
    # Add statistics
    quizzes = quizzes.annotate(
        total_questions=Count('questions'),
        total_attempts=Count('quizattempt'),
        avg_score=Avg('quizattempt__score')
    )
    
    # Handle sorting
    sort_param = request.GET.get('sort')
    if sort_param:
        if sort_param == 'difficulty':
            quizzes = quizzes.order_by('difficulty_level')
        elif sort_param == 'attempts':
            quizzes = quizzes.order_by('-total_attempts')
        elif sort_param == 'score':
            quizzes = quizzes.order_by('-avg_score')
        elif sort_param == 'date':
            quizzes = quizzes.order_by('-created_at')
        elif sort_param == 'title':
            quizzes = quizzes.order_by('title')
    else:
        quizzes = quizzes.order_by('-created_at')
    
    context = {
        'quizzes': quizzes,
        'search_term': search_term,
        'current_sort': sort_param,
        'current_filter': filter_type
    }
    
    return render(request, 'quiz/quiz_list.html', context)

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, is_active=True)
    
    # Get or create attempt
    attempt, created = QuizAttempt.objects.get_or_create(
        quiz=quiz,
        user=request.user,
        is_completed=False
    )
    
    # Get current question
    answered_questions = attempt.answers.values_list('question_id', flat=True)
    current_question = quiz.questions.exclude(id__in=answered_questions).first()
    
    if not current_question:
        # All questions answered
        return redirect('quiz:submit', quiz_id=quiz.id)
    
    context = {
        'quiz': quiz,
        'attempt': attempt,
        'question': current_question,
        'current_question_number': len(answered_questions) + 1,
        'total_questions': quiz.questions.count(),
        'is_last_question': len(answered_questions) + 1 == quiz.questions.count()
    }
    
    return render(request, 'quiz/take_quiz.html', context)

@csrf_protect
@login_required
def submit_quiz(request, quiz_id):
    if request.method != 'POST':
        return redirect('quiz:list')
        
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    attempt = get_object_or_404(
        QuizAttempt,
        quiz=quiz,
        user=request.user,
        is_completed=False
    )
    
    # Process answer
    question_id = request.POST.get('question_id')
    selected_answer = request.POST.get('answer')
    
    if question_id and selected_answer:
        question = get_object_or_404(Question, id=question_id)
        Answer.objects.create(
            attempt=attempt,
            question=question,
            selected_answer=selected_answer,
            is_correct=selected_answer == question.correct_answer
        )
    
    # Check if all questions are answered
    if attempt.answers.count() == quiz.questions.count():
        # Calculate score
        correct_answers = attempt.answers.filter(is_correct=True).count()
        total_questions = quiz.questions.count()
        score = (correct_answers / total_questions) * 100
        
        attempt.score = score
        attempt.completed_at = timezone.now()
        attempt.is_completed = True
        attempt.save()
        
        messages.success(request, f"Quiz completed! Your score: {score:.1f}%")
        return redirect('quiz:results', attempt_id=attempt.id)
    
    return redirect('quiz:take', quiz_id=quiz.id)

@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, pk=attempt_id, user=request.user)
    return render(request, 'quiz/quiz_results.html', {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'answers': attempt.answers.all()
    })

@login_required
def edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, creator=request.user)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            form.save()
            messages.success(request, 'Quiz updated successfully!')
            return redirect('quiz:list')
    else:
        form = QuizForm(instance=quiz)
    
    return render(request, 'quiz/quiz_form.html', {
        'form': form,
        'quiz': quiz,
        'title': 'Edit Quiz'
    })

@login_required
def quiz_stats(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    if quiz.creator != request.user:
        messages.error(request, "You don't have permission to view these statistics.")
        return redirect('quiz:list')
    
    attempts = QuizAttempt.objects.filter(quiz=quiz, is_completed=True)
    
    # Calculate statistics
    total_attempts = attempts.count()
    average_score = attempts.aggregate(Avg('score'))['score__avg'] or 0
    pass_rate = (attempts.filter(score__gte=quiz.passing_score).count() / total_attempts * 100) if total_attempts > 0 else 0
    
    # Get recent attempts
    recent_attempts = attempts.select_related('user').order_by('-completed_at')[:10]
    
    stats = {
        "total_attempts": total_attempts,
        "average_score": average_score,
        "pass_rate": pass_rate,
    }
    
    context = {
        'quiz': quiz,
        'stats': stats,
        'attempts': recent_attempts,
    }
    
    return render(request, 'quiz/quiz_stats.html', context)

@login_required
def add_quiz(request):
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.creator = request.user
            quiz.save()
            messages.success(request, 'Quiz created successfully!')
            return redirect('quiz:edit', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    return render(request, 'quiz/quiz_form.html', {'form': form, 'title': 'Create Quiz'})

@login_required
def quiz_delete(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    
    # Check if user is the quiz creator
    if request.user != quiz.creator:
        messages.error(request, "You don't have permission to delete this quiz!")
        return redirect('quiz:list')
    
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, "Quiz deleted successfully!")
        return redirect('quiz:list')
        
    return render(request, 'quiz/quiz_confirm_delete.html', {'quiz': quiz})

@login_required
def add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id, creator=request.user)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            
            messages.success(request, 'Question added successfully!')
            return redirect('quiz:edit', quiz_id=quiz.id)
    else:
        form = QuestionForm()
    
    return render(request, 'quiz/question_form.html', {
        'form': form,
        'quiz': quiz,
        'title': 'Add Question'
    })

@login_required
def edit_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    quiz = question.quiz
    
    if quiz.creator != request.user:
        messages.error(request, "You don't have permission to edit this question.")
        return redirect('quiz:list')
    
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            return redirect('quiz:edit', quiz_id=quiz.id)
    else:
        form = QuestionForm(instance=question)
    
    return render(request, 'quiz/question_form.html', {
        'form': form,
        'quiz': quiz,
        'question': question,
        'title': 'Edit Question'
    })

@login_required
def delete_question(request, question_id):
    if request.method == 'POST':
        question = get_object_or_404(Question, pk=question_id)
        quiz = question.quiz
        
        if quiz.creator != request.user:
            messages.error(request, "You don't have permission to delete this question.")
            return redirect('quiz:list')
        
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('quiz:edit', quiz_id=quiz.id)
    
    return HttpResponseNotAllowed(['POST'])
