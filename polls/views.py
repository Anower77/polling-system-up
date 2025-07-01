from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.contrib import messages
from .models import Poll, Choice, Vote
from .forms import PollAddForm, EditPollForm, ChoiceAddForm
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings  # To access your email settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.forms import inlineformset_factory
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from rest_framework import viewsets, permissions
from .serializers import PollSerializer, ChoiceSerializer, VoteSerializer
from rest_framework.response import Response
from rest_framework.decorators import action


@login_required()
def polls_list(request):
    polls = Poll.objects.all()
    search_term = request.GET.get('search', '')
    
    # Filter by search term if provided
    if search_term:
        polls = polls.filter(
            Q(text__icontains=search_term) |
            Q(owner__username__icontains=search_term)
        )
    
    # Annotate vote count
    polls = polls.annotate(total_votes=Count('vote'))
    
    # Sort by different criteria
    sort = request.GET.get('sort', '-pub_date')
    vote_sort = request.GET.get('vote')
    
    if vote_sort:
        polls = polls.order_by('-total_votes')
    else:
        polls = polls.order_by(sort)
    
    paginator = Paginator(polls, 6)
    page = request.GET.get("page")
    polls = paginator.get_page(page)

    get_dict_copy = request.GET.copy()
    params = get_dict_copy.pop("page", True) and get_dict_copy.urlencode()

    context = {
        "polls": polls,
        "params": params,
        "search_term": search_term,
    }
    return render(request, "polls/polls_list.html", context)


@login_required()
def dashboard(request):
    polls = Poll.objects.all()
    poll_data = []

    for poll in polls:
        unique_voters = Vote.objects.filter(poll=poll).values("user").distinct().count()
        poll_data.append({"question": poll.text, "unique_voters": unique_voters})

    context = {"poll_data": poll_data}
    return render(request, "polls/dashboard.html", context)


@login_required()
def list_by_user(request):
    all_polls = Poll.objects.filter(owner=request.user)
    paginator = Paginator(all_polls, 7)  # Show 7 contacts per page

    page = request.GET.get("page")
    polls = paginator.get_page(page)

    context = {
        "polls": polls,
    }
    return render(request, "polls/polls_list.html", context)


@login_required(login_url='accounts:login')
def polls_add(request):
    if request.method == "POST":
        form = PollAddForm(request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.owner = request.user
            poll.save()
            Choice(poll=poll, choice_text=form.cleaned_data["choice1"]).save()
            Choice(poll=poll, choice_text=form.cleaned_data["choice2"]).save()

            messages.success(
                request,
                "Poll & Choices added successfully.",
                extra_tags="alert alert-success alert-dismissible fade show",
            )

            return redirect("polls:list")
    else:
        form = PollAddForm()
    context = {
        "form": form,
    }
    return render(request, "polls/add_poll.html", context)


@login_required
def polls_edit(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    if request.user != poll.owner:
        return redirect("home")
        
    ChoiceFormSet = inlineformset_factory(
        Poll, 
        Choice,
        fields=('choice_text',),
        extra=1,
        can_delete=True
    )
    
    if request.method == 'POST':
        form = EditPollForm(request.POST, instance=poll)
        formset = ChoiceFormSet(request.POST, instance=poll)
        
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(
                request,
                "Poll Updated successfully.",
                extra_tags="alert alert-success alert-dismissible fade show",
            )
            return redirect('polls:list')
    else:
        form = EditPollForm(instance=poll)
        formset = ChoiceFormSet(instance=poll)
    
    return render(request, 'polls/poll_edit.html', {
        'form': form,
        'choice_formset': formset,
        'poll': poll
    })


@login_required
def poll_delete(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    
    # Check if user is the poll owner
    if request.user != poll.owner:
        messages.error(request, "You don't have permission to delete this poll!")
        return redirect('polls:list')
    
    if request.method == 'POST':
        poll.delete()
        messages.success(request, "Poll deleted successfully!")
        return redirect('polls:list')
        
    return render(request, 'polls/poll_confirm_delete.html', {'poll': poll})


@login_required
def add_choice(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if request.user != poll.owner:
        return redirect("home")

    if request.method == "POST":
        form = ChoiceAddForm(request.POST)
        if form.is_valid:
            new_choice = form.save(commit=False)
            new_choice.poll = poll
            new_choice.save()
            messages.success(
                request,
                "Choice added successfully.",
                extra_tags="alert alert-success alert-dismissible fade show",
            )
            return redirect("polls:edit", poll.id)
    else:
        form = ChoiceAddForm()
    context = {
        "form": form,
    }
    return render(request, "polls/add_choice.html", context)


@login_required
def choice_edit(request, choice_id):
    choice = get_object_or_404(Choice, pk=choice_id)
    poll = get_object_or_404(Poll, pk=choice.poll.id)
    if request.user != poll.owner:
        return redirect("home")

    if request.method == "POST":
        form = ChoiceAddForm(request.POST, instance=choice)
        if form.is_valid:
            new_choice = form.save(commit=False)
            new_choice.poll = poll
            new_choice.save()
            messages.success(
                request,
                "Choice Updated successfully.",
                extra_tags="alert alert-success alert-dismissible fade show",
            )
            return redirect("polls:edit", poll.id)
    else:
        form = ChoiceAddForm(instance=choice)
    context = {
        "form": form,
        "edit_choice": True,
        "choice": choice,
    }
    return render(request, "polls/add_choice.html", context)


@login_required
def choice_delete(request, choice_id):
    choice = get_object_or_404(Choice, pk=choice_id)
    poll = get_object_or_404(Poll, pk=choice.poll.id)
    if request.user != poll.owner:
        return redirect("home")
    choice.delete()
    messages.success(
        request,
        "Choice Deleted successfully.",
        extra_tags="alert alert-success alert-dismissible fade show",
    )
    return redirect("polls:edit", poll.id)


@login_required
def poll_detail(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    
    # Get vote statistics
    total_votes = poll.get_vote_count()
    votes_per_day = total_votes / max((timezone.now() - poll.pub_date).days, 1)
    
    # Get user's vote if they have voted
    user_choice = None
    if request.user.is_authenticated:
        try:
            vote = Vote.objects.get(user=request.user, poll=poll)
            user_choice = vote.choice
        except Vote.DoesNotExist:
            pass
    
    context = {
        'poll': poll,
        'user_choice': user_choice,
        'total_votes': total_votes,
        'votes_per_day': votes_per_day,
    }
    
    return render(request, 'polls/poll_detail.html', context)


@csrf_protect
@login_required(login_url='accounts:login')
def poll_vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    
    # Check if poll is active
    if not poll.active:
        messages.error(
            request,
            "This poll is closed!",
            extra_tags='alert alert-warning alert-dismissible fade show'
        )
        return redirect('polls:detail', poll_id=poll_id)
    
    # Check if user is poll owner
    if request.user == poll.owner:
        messages.error(
            request,
            "You cannot vote on your own poll!",
            extra_tags='alert alert-warning alert-dismissible fade show'
        )
        return redirect('polls:detail', poll_id=poll_id)
    
    # Check if user has already voted
    if Vote.objects.filter(user=request.user, poll=poll).exists():
        messages.error(
            request,
            "You have already voted on this poll!",
            extra_tags='alert alert-warning alert-dismissible fade show'
        )
        return redirect('polls:detail', poll_id=poll_id)
    
    if request.method == 'POST':
        try:
            choice_id = request.POST.get('choice')
            if not choice_id:
                messages.error(
                    request,
                    "Please select a choice!",
                    extra_tags='alert alert-danger alert-dismissible fade show'
                )
                return redirect('polls:detail', poll_id=poll_id)
            
            choice = poll.choice_set.get(pk=choice_id)
            
            # Create vote
            Vote.objects.create(
                user=request.user,
                poll=poll,
                choice=choice
            )

            messages.success(
                request,
                "Your vote has been recorded!",
                extra_tags='alert alert-success alert-dismissible fade show'
            )
            return redirect('polls:detail', poll_id=poll_id)
            
        except Choice.DoesNotExist:
            messages.error(
                request,
                "Invalid choice selected!",
                extra_tags='alert alert-danger alert-dismissible fade show'
            )
            return redirect('polls:detail', poll_id=poll_id)
    
    return redirect('polls:detail', poll_id=poll_id)


@login_required
def end_poll(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if request.user != poll.owner:
        return redirect("home")

    if poll.active is True:
        poll.active = False
        poll.save()
        return render(request, "polls/poll_result.html", {"poll": poll})
    else:
        return render(request, "polls/poll_result.html", {"poll": poll})


def poll_results(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    votes = Vote.objects.filter(poll=poll).select_related('choice', 'user')
    
    # Calculate vote percentages
    total_votes = votes.count()
    choices_with_stats = []
    
    for choice in poll.choice_set.all():
        choice_votes = votes.filter(choice=choice).count()
        percentage = (choice_votes / total_votes * 100) if total_votes > 0 else 0
        choices_with_stats.append({
            'choice': choice,
            'votes': choice_votes,
            'percentage': round(percentage, 1)
        })
    
    context = {
        'poll': poll,
        'choices_with_stats': choices_with_stats,
        'total_votes': total_votes,
    }
    return render(request, 'polls/poll_results.html', context)


class PollViewSet(viewsets.ModelViewSet):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        choice = self.get_object()
        user = request.user
        
        # Check if user already voted for this poll
        if Vote.objects.filter(choice__poll=choice.poll, user=user).exists():
            return Response({'detail': 'You have already voted in this poll.'}, status=400)
        
        vote = Vote.objects.create(choice=choice, poll=choice.poll, user=user)
        serializer = VoteSerializer(vote)
        return Response(serializer.data)


class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@login_required
def vote(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    
    # Check if user can vote
    if not poll.user_can_vote(request.user):
        messages.error(request, "You have already voted in this poll!")
        return redirect('polls:detail', poll_id=poll_id)
    
    # Check if user is poll owner
    if request.user == poll.owner:
        messages.error(request, "You cannot vote on your own poll!")
        return redirect('polls:detail', poll_id=poll_id)
    
    try:
        selected_choice = poll.choice_set.get(pk=request.POST['choice'])
        
        # Create vote
        Vote.objects.create(
            user=request.user,
            poll=poll,
            choice=selected_choice
        )

        messages.success(request, "Your vote has been recorded!")
        return redirect('polls:detail', poll_id=poll_id)
        
    except (KeyError, Choice.DoesNotExist):
        messages.error(request, "You didn't select a choice!")
        return redirect('polls:detail', poll_id=poll_id)
