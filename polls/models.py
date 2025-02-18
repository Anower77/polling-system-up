from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import secrets
from django.urls import reverse
from django.conf import settings
from django.db.models import Count


class Poll(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_vote_count(self):
        return Vote.objects.filter(poll=self).count()

    def user_can_vote(self, user):
        """
        Return True if user can vote in this poll.
        """
        if not user.is_authenticated:
            return False
        if user == self.owner:
            return False
        return not Vote.objects.filter(poll=self, user=user).exists()

    @property
    def vote_count(self):
        return self.vote_set.count()

    def get_result_dict(self):
        res = []
        for choice in self.choice_set.all():
            d = {}
            alert_class = ['primary', 'secondary', 'success',
                           'danger', 'dark', 'warning', 'info']

            d['alert_class'] = secrets.choice(alert_class)
            d['text'] = choice.choice_text
            d['num_votes'] = choice.get_vote_count
            if not self.vote_count:
                d['percentage'] = 0
            else:
                d['percentage'] = (choice.get_vote_count /
                                   self.vote_count)*100

            res.append(d)
        return res

    def get_share_url(self):
        """Get the absolute URL for sharing"""
        return reverse('polls:detail', kwargs={'poll_id': self.id})

    def __str__(self):
        return self.text


class Choice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='choice_set')
    choice_text = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    votes = models.IntegerField(default=0)

    @property
    def get_vote_count(self):
        return self.vote_set.count()

    def get_vote_percentage(self):
        total_votes = self.poll.get_vote_count()
        if total_votes == 0:
            return 0
        return (self.votes / total_votes) * 100

    def __str__(self):
        return f"{self.poll.text[:25]} - {self.choice_text[:25]}"


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, related_name='vote_set')
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'poll')

    def __str__(self):
        return f"{self.user.username} - {self.choice.choice_text}"

    def save(self, *args, **kwargs):
        if not self.poll_id:  # Only set if not already set
            self.poll = self.choice.poll
        super().save(*args, **kwargs)
