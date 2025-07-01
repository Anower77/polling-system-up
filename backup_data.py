import os
import django
import json
from django.core import serializers

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'polling.settings')
django.setup()

from polls.models import *
from quiz.models import *
from accounts.models import *
from payment.models import *

def backup_data():
    # List of models to backup
    models = [Poll, Choice, Vote, Quiz, Question, QuizAttempt, Answer, Subscription, Payment]
    
    for model in models:
        data = serializers.serialize('json', model.objects.all())
        filename = f'backup_{model.__name__.lower()}.json'
        
        with open(filename, 'w') as f:
            f.write(data)
        
        print(f'Backed up {model.__name__}')

if __name__ == "__main__":
    backup_data() 