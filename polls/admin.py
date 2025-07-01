from django.contrib import admin
from .models import Poll, Choice, Vote


class ChoiceInline(admin.TabularInline):  # or admin.StackedInline for a different layout
    model = Choice
    extra = 1

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ["text", "owner", "pub_date", "active"]
    search_fields = ["text", "owner__username"]
    list_filter = ["active", 'pub_date']
    date_hierarchy = "pub_date"
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ["choice_text", "poll", "votes"]
    search_fields = ["choice_text", "poll__text"]
    list_filter = ["poll"]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["user", "choice", "created_at"]
    search_fields = ["user__username", "choice__choice_text"]
    autocomplete_fields = ["user", "choice"]
    date_hierarchy = "created_at"
