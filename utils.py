import datetime
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Sum

from quanda.models import Question, QuestionVote, Profile, Answer, AnswerVote

QUESTION_VOTED_UP = getattr(settings, 'QUESTION_VOTED_UP', 10)
QUESTION_VOTED_DOWN = getattr(settings, 'QUESTION_VOTED_DOWN', 5)
ANSWER_VOTED_UP = getattr(settings, 'ANSWER_VOTED_UP', 10)
ANSWER_VOTED_DOWN = getattr(settings, 'ANSWER_VOTED_DOWN', 5)

def get_user_rep(username):
    """
    Returns a user's rep, calculated by based on base rep (usually 0 unless
    otherwise assigned by an admin) plus questions and answers being
    voted up or down
    """
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return 0

    profile = Profile.objects.get_or_create(user=user)[0]    
    score = profile.reputation

    for question in Question.objects.filter(author=profile.user):
         for question_vote in QuestionVote.objects.filter(question=question):
            if question_vote.score == 1:
                score += QUESTION_VOTED_UP
            elif question_vote.score == -1:
                score += QUESTION_VOTED_DOWN

    for answer in Answer.objects.filter(author=profile.user):
        for answer_vote in AnswerVote.objects.filter(answer=answer):
            if answer_vote.score == 1:
                score += ANSWER_VOTED_UP
            elif answer_vote.score == -1:
                score += ANSWER_VOTED_DOWN

    return score
    
def strip_js(html_string):
    """
    This function should remove any javascript from an html string. For now,
    it simply replaces any occurence of <script with an empty string
    """
    return re.sub('<script', '', html_string)
    
def smart_date(event_date):
    """
    Function that formats a datetime object depending on how long it's been
    since that event

    """
    
    now = datetime.datetime.now()
    delta = now - event_date
    
    if delta.days < 1:
        format = "%I:%M %p"
    elif delta.days < 364:
        format = "%b %d"
    else:
        format = "%b %d %Y"
        
    return event_date.strftime(format)
    
    
    