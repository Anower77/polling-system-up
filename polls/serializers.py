from rest_framework import serializers
from .models import Poll, Choice, Vote

class ChoiceSerializer(serializers.ModelSerializer):
    votes_count = serializers.SerializerMethodField()

    class Meta:
        model = Choice
        fields = ['id', 'choice_text', 'votes_count']

    def get_votes_count(self, obj):
        return obj.vote_set.count()

class PollSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    created_by = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Poll
        fields = ['id', 'text', 'created_by', 'pub_date', 'active', 'choices']
        read_only_fields = ['pub_date', 'active']

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ['id', 'choice', 'poll', 'user']
        
    def validate(self, attrs):
        if attrs['choice'].poll != attrs['poll']:
            raise serializers.ValidationError('Choice does not belong to poll')
        return attrs 