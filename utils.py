from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Sum

from quanda.models import Question, QuestionVote, Profile

vote_question_down_price = getattr(settings, 'VOTE_QUESTION_DOWN_PRICE', 2)
vote_question_up_price = getattr(settings, 'VOTE_QUESTION_UP_PRICE', 0)


def get_user_rep(username):
    """Returns a user's rep, calculated by:
    - the number of up votes minus the number of down votes on each question
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return 0

    profile = Profile.objects.get_or_create(user=user)[0]    
    score = profile.reputation

    for question in Question.objects.filter(author=profile.user):
         for question_vote in QuestionVote.objects.filter(question=question):
            #TODO: this can probably be done via aggregation
            score += question_vote.score
         
    return score
    
