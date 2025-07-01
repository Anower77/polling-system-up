from rest_framework import serializers
from .models import Quiz, Question, QuizAttempt, Answer

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'option1', 'option2', 'option3', 'option4']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')
    total_questions = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'creator', 'created_at', 
                 'time_limit', 'is_active', 'passing_score', 'questions',
                 'total_questions', 'total_points']

    def get_total_questions(self, obj):
        return obj.questions.count()

    def get_total_points(self, obj):
        return sum(question.points for question in obj.questions.all())

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'attempt', 'question', 'selected_answer', 'is_correct']

class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    user = serializers.ReadOnlyField(source='user.username')
    time_taken = serializers.ReadOnlyField()

    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'user', 'score', 'started_at', 
                 'completed_at', 'is_completed', 'time_taken', 'answers']

class QuizSubmissionSerializer(serializers.Serializer):
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
