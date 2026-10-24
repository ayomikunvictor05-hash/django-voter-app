from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import Count
from django.utils import timezone

from .models import Poll, Choice, Vote
from .forms import PollForm, CodeSearchForm, PasscodeVerifyForm


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@login_required
def dashboard(request):
    search_form = CodeSearchForm()
    created_polls = Poll.objects.filter(creator=request.user).order_by('-created_at')
    voted_votes = Vote.objects.filter(voter=request.user).select_related('poll', 'choice').order_by('-created_at')

    context = {
        'search_form': search_form,
        'created_polls': created_polls,
        'voted_votes': voted_votes,
    }
    return render(request, 'polls/dashboard.html', context)


@login_required
def create_poll(request):
    if request.method == 'POST':
        form = PollForm(request.POST)
        options = [opt.strip() for opt in request.POST.getlist('options') if opt.strip()]
        option_images = request.FILES.getlist('option_images')

        if form.is_valid():
            if len(options) < 2:
                messages.error(request, "You must provide at least 2 voting options.")
            else:
                poll = form.save(commit=False)
                poll.creator = request.user

                selected_checkboxes = form.cleaned_data.get('domain_checkboxes', [])
                custom = form.cleaned_data.get('custom_domains', '').strip()

                if 'ALL' in selected_checkboxes or not selected_checkboxes:
                    poll.allowed_domains = ''
                else:
                    domains = list(selected_checkboxes)
                    if custom:
                        domains.extend([d.strip().lower().lstrip('@') for d in custom.split(',') if d.strip()])
                    poll.allowed_domains = ','.join(set(domains))

                poll.save()

                # Save choices with optional images
                for index, opt_text in enumerate(options):
                    img = option_images[index] if index < len(option_images) else None
                    Choice.objects.create(poll=poll, option_text=opt_text, image=img)

                messages.success(request, f"Poll created successfully!")
                return redirect('poll_detail', code=poll.unique_code)
    else:
        form = PollForm()

    return render(request, 'polls/create_poll.html', {'form': form})


@login_required
def search_poll(request):
    """Stores code in session to mask URL path."""
    if request.method == 'POST':
        form = CodeSearchForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code'].strip().upper()
            try:
                poll = Poll.objects.get(unique_code=code)
                # Mask URL by storing code in session
                request.session['active_voting_code'] = poll.unique_code
                return redirect('vote_ballot')
            except Poll.DoesNotExist:
                messages.error(request, f"No voting avenue found with code '{code}'.")
    return redirect('dashboard')


@login_required
def vote_ballot(request):
    """Secure ballot view using session token lookup."""
    code = request.session.get('active_voting_code')
    if not code:
        messages.error(request, "Please enter a voting code to access a ballot.")
        return redirect('dashboard')

    poll = get_object_or_404(Poll, unique_code=code)
    user = request.user
    now = timezone.now()

    # 1. Scheduled Time Check (Observation 1)
    if poll.is_upcoming():
        messages.warning(
            request,
            f"Voting for this poll has not started yet. It opens on {poll.start_time.strftime('%b %d, %Y at %H:%M')}."
        )
        return redirect('dashboard')

    if now > poll.end_time or poll.status != Poll.Status.ACTIVE:
        messages.warning(request, "This voting avenue has ended or is currently paused.")
        return redirect('poll_results', code=poll.unique_code)

    # 2. Check if user already voted (Creators can vote if they haven't voted yet)
    existing_vote = Vote.objects.filter(poll=poll, voter=user).first()
    if existing_vote:
        messages.info(request, "You have already cast your vote in this poll.")
        return redirect('poll_results', code=poll.unique_code)

    # 3. Eligibility Checks
    allowed_domains = poll.get_allowed_domains_list()
    if allowed_domains and user.email_domain not in allowed_domains:
        messages.error(request, f"Eligibility Error: Domain @{user.email_domain} is not authorized.")
        return redirect('dashboard')

    if poll.allowed_voter_group and user.voter_group.lower() != poll.allowed_voter_group.lower():
        messages.error(request, f"Eligibility Error: Restricted to group '{poll.allowed_voter_group}'.")
        return redirect('dashboard')

    # 4. Passcode Verification
    if poll.passcode:
        session_key = f"passcode_verified_{poll.id}"
        if not request.session.get(session_key, False):
            if request.method == 'POST' and 'verify_passcode' in request.POST:
                pass_form = PasscodeVerifyForm(request.POST)
                if pass_form.is_valid() and pass_form.cleaned_data['passcode'] == poll.passcode:
                    request.session[session_key] = True
                    return redirect('vote_ballot')
                else:
                    messages.error(request, "Invalid passcode provided.")
            else:
                pass_form = PasscodeVerifyForm()
            return render(request, 'polls/passcode_verify.html', {'poll': poll, 'form': pass_form})

    # 5. Process Vote Submission
    if request.method == 'POST' and 'choice_id' in request.POST:
        choice_id = request.POST.get('choice_id')
        choice = get_object_or_404(Choice, id=choice_id, poll=poll)

        try:
            with transaction.atomic():
                vote = Vote.objects.create(
                    poll=poll,
                    choice=choice,
                    voter=user,
                    ip_address=get_client_ip(request)
                )
            messages.success(request, f"Vote submitted! Receipt: {vote.receipt_token}")
            return redirect('poll_results', code=poll.unique_code)
        except IntegrityError:
            messages.error(request, "Double-voting blocked: You have already voted.")
            return redirect('poll_results', code=poll.unique_code)

    return render(request, 'polls/vote_ballot.html', {'poll': poll})


@login_required
def poll_results(request, code):
    poll = get_object_or_404(Poll, unique_code=code)
    now = timezone.now()
    user_vote = Vote.objects.filter(poll=poll, voter=request.user).first()

    can_view_results = (
        poll.results_visibility == Poll.ResultsVisibility.REALTIME
        or now > poll.end_time
        or poll.creator == request.user
    )

    choices_data = []
    total_votes = poll.votes.count()

    if can_view_results:
        choices_qs = poll.choices.annotate(vote_count=Count('votes'))
        for choice in choices_qs:
            percentage = round((choice.vote_count / total_votes * 100), 1) if total_votes > 0 else 0
            choices_data.append({
                'id': choice.id,
                'option_text': choice.option_text,
                'image_url': choice.image.url if choice.image else None,
                'vote_count': choice.vote_count,
                'percentage': percentage,
            })

    context = {
        'poll': poll,
        'user_vote': user_vote,
        'can_view_results': can_view_results,
        'total_votes': total_votes,
        'choices_data': choices_data,
    }
    return render(request, 'polls/results.html', context)


@login_required
def poll_detail(request, code):
    poll = get_object_or_404(Poll, unique_code=code, creator=request.user)
    total_votes = poll.votes.count()
    choices = poll.choices.annotate(vote_count=Count('votes'))

    context = {
        'poll': poll,
        'total_votes': total_votes,
        'choices': choices,
    }
    return render(request, 'polls/poll_detail.html', context)