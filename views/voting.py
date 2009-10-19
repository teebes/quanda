from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from quanda.models import Question, QuestionVote, Answer, AnswerVote
from quanda.utils import get_user_rep
from quanda.views import question_read

def question_adjust_vote(request, question_id, delta=0):
    vote_question_up_rep = getattr(settings, 'VOTE_QUESTION_UP_REP', 20)
    vote_question_down_rep = getattr(settings, 'VOTE_QUESTION_DOWN_REP', 100)
    
    if not request.user.is_authenticated():
        if delta == 1:
            msg = "You need to sign up and get at least %s rep to vote up a question" % vote_question_up_rep
        elif delta == -1:
            msg = "You need to sign up and get at least %s rep to vote down a question" % vote_question_down_rep
        else: msg = None
        return question_read(request, question_id, context={'msg': msg})
    
    if delta == 1 and get_user_rep(request.user.username) < vote_question_up_rep:
        return question_read(
            request,
            question_id,
            context={'msg': "You need at least %s rep to vote up a question"\
                     % vote_question_up_rep}
        )
    elif delta == -1 and get_user_rep(request.user.username) < vote_question_down_rep:
        return question_read(
            request,
            question_id,
            context={'msg': "You need at least %s rep to vote down a question"\
                    % vote_question_down_rep}
        )
    
    question = get_object_or_404(Question, pk=question_id)

    if request.user == question.author:
        return question_read(
            request,
            question_id,
            context={'msg': "You cannot vote on your own questions"}
        )

    try:
        question_vote = QuestionVote.objects.get(question=question, user=request.user)
    except QuestionVote.DoesNotExist:
        question_vote = QuestionVote(question=question, user=request.user)    
    question_vote.score = delta
    question_vote.save()
    return HttpResponseRedirect(reverse('quanda_question_read', args=[question_id]))

def answer_adjust_vote(request, answer_id, delta=0):
    answer = get_object_or_404(Answer, pk=answer_id)
    
    vote_answer_up_rep = getattr(settings, 'VOTE_ANSWER_UP_REP', 20)
    vote_answer_down_rep = getattr(settings, 'VOTE_ANSWER_DOWN_REP', 100)
    
    if not request.user.is_authenticated():
        if delta == 1:
            msg = "You need to sign up and get at least %s rep to vote up an answer" % vote_answer_up_rep
        elif delta == -1:
            msg = "You need to sign up and get at least %s rep to vote down an answer" % vote_answer_down_rep
        else: msg = None
        return question_read(request, answer.question.id, context={'msg': msg})
        
    if delta == 1 and get_user_rep(request.user.username) < vote_answer_up_rep:
        return question_read(
            request,
            answer.question.id,
            context={'msg': "You need at least %s rep to vote up an answer"\
                     % vote_answer_up_rep}
        )
    elif delta == -1 and get_user_rep(request.user.username) < vote_answer_down_rep:
        return question_read(
            request,
            answer.question.id,
            context={'msg': "You need at least %s rep to vote down an answer"\
                    % vote_answer_down_rep}
        )    
    
    if request.user == answer.author:
        return question_read(
            request,
            answer.question_id,
            context={'msg': "You cannot vote on your own answers"}
        )
    
    try:
        answer_vote = AnswerVote.objects.get(answer=answer, user=request.user)
    except AnswerVote.DoesNotExist:
        answer_vote = AnswerVote(answer=answer, user=request.user)
    answer_vote.score = delta
    answer_vote.save()
    return HttpResponseRedirect(reverse('quanda_question_read', args=[answer.question.id]))
    