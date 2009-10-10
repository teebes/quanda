from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from quanda.forms import QuestionForm, QuestionTagForm, QuestionListForm, QuestionListOrderForm, AnswerForm, RepForm
from quanda.models import Question, QuestionVote, QuestionTag, QuestionList, QuestionListOrder, Answer, AnswerVote, Profile
from quanda.utils import get_user_rep

def index(request):
    #if request.user.is_authenticated():
    #    rep = get_user_rep(request.user)
    #else:
    #    rep = None
    
    #return HttpResponse(get_user_rep(request.user.username))
    
    questions = Question.objects.all()
    
    # figure out which questions have the highest scores
    # TODO: this really needs to be optimized, doing a raw approach for now
    # just to get stuff up and running
    top_questions = []
    for question in questions:
        top_questions.append({
            'question': question,
            'score': question.get_score()
        })
    top_questions.sort(lambda x, y: x['score'] - y['score'], reverse=True)
    
    if request.user.is_authenticated():
        your_answers = Answer.objects.filter(question__author=request.user).order_by("-posted")
    else:
        your_answers = None

    return render_to_response('quanda/index.html', {
        'questions': Question.objects.all(),
        'questions_manager': Question.objects,
        #'rep': rep,
        
        'top_questions': top_questions[:5],
        'recent_questions': questions.order_by("-posted")[:5],
        'your_answers': your_answers,
        }, context_instance=RequestContext(request))

def search(request):
    return HttpResponse("search")

def question_create_edit(request, question_id=None):
    try:
        question = Question.objects.get(pk=question_id)
        if not request.user.is_authenticated() or request.user.username != question.author.username:
            return HttpResponse("You are not allowed to edit this post.")
    except Question.DoesNotExist:
        question = None
        
    if request.method == 'POST':
        form = QuestionForm(request.user, request.POST, instance=question)
        if form.is_valid():
            question = form.save()
            return HttpResponseRedirect(reverse('quanda_question_read', args=[question.id]))
    else:
        form = QuestionForm(request.user, instance=question)
    
    return render_to_response('quanda/question_create_edit.html', {
        'form': form,
        }, context_instance=RequestContext(request))

    
def question_read(request, question_id=None, msg=None, context={}):
    question = get_object_or_404(Question, pk=question_id)
    
    # user answer question
    if request.method == "POST":
        answer_form = AnswerForm(request.user, question, request.POST)
        if answer_form.is_valid():
            answer = answer_form.save()
            return HttpResponseRedirect(reverse('quanda_question_read', args=[question_id]))
    else:
        answer_form = AnswerForm(request.user, question)
        
    # get how the user previously voted on this question
    try:
        user_question_previous_vote = QuestionVote.objects.get(question=question, user=request.user).score
    except Exception:
        user_question_previous_vote = 0

    # get questions related to this one
    #return HttpResponse(question.tags.all())
    related_questions = Question.objects.filter(tags__title__in=question.tags.all())

    answers_q = Answer.objects\
                .filter(question=question)\
                .annotate(score=Sum('answervotes__score'))\
                .order_by('-posted')\
                .order_by('-score')\
                .order_by('-user_chosen')    

    # This block defines an 'answers' list of Answer objects with an extra
    # 'user_prev_vote' attribute indicating the user's last vote on that answer
    answers = []
    for answer in answers_q:
        try:
            answer_vote = AnswerVote.objects.get(answer=answer, user=request.user).score
        except Exception:
            answer_vote = 0
        answer.user_prev_vote = answer_vote
        answers.append(answer)

    context['question'] = question
    context['user_question_previous_vote'] = user_question_previous_vote
    context['related_questions'] = related_questions
    context['answer_form'] = answer_form
    context['answers'] = answers

    return render_to_response('quanda/question_read.html',
                               context,
                               context_instance=RequestContext(request))

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
        
    if delta == 1 and get_user_rep(request.user) < vote_question_up_rep:
        return question_read(
            request,
            question_id,
            context={'msg': "You need at least %s rep to vote up a question"\
                     % vote_question_up_rep}
        )
    elif delta == -1 and get_user_rep(request.user) < vote_question_down_rep:
        return question_read(
            request,
            question_id,
            context={'msg': "You need at least %s rep to vote down a question"\
                    % vote_question_down_rep}
        )
    
    question = get_object_or_404(Question, pk=question_id)
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
        
    if delta == 1 and get_user_rep(request.user) < vote_answer_up_rep:
        return question_read(
            request,
            answer.question.id,
            context={'msg': "You need at least %s rep to vote up an answer"\
                     % vote_answer_up_rep}
        )
    elif delta == -1 and get_user_rep(request.user) < vote_answer_down_rep:
        return question_read(
            request,
            answer.question.id,
            context={'msg': "You need at least %s rep to vote down an answer"\
                    % vote_answer_down_rep}
        )    
    
    try:
        answer_vote = AnswerVote.objects.get(answer=answer, user=request.user)
    except AnswerVote.DoesNotExist:
        answer_vote = AnswerVote(answer=answer, user=request.user)
    answer_vote.score = delta
    answer_vote.save()
    return HttpResponseRedirect(reverse('quanda_question_read', args=[answer.question.id]))
    
@login_required
def pick_answer(request, answer_id=None):
    try:
        answer = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        raise Http404
    
    if answer.question.author != request.user:
        return HttpResponse("This is not your question to answer")
    
    try:
        already_chosen = Answer.objects.get(question=answer.question, user_chosen=True)
        already_chosen.user_chosen = False
        already_chosen.save()
    except Answer.DoesNotExist: pass

    answer.user_chosen = True
    answer.save()
    
    return HttpResponseRedirect(reverse('quanda_question_read', args=[answer.question.id]))

@login_required # TODO: staff only
def tags_admin(request):
    if request.method == 'POST':
        new_tag_form = QuestionTagForm(request.POST)
        if new_tag_form.is_valid():
            new_tag = new_tag_form.save()
            return HttpResponseRedirect(reverse('quanda_tags_admin'))
    else:
        new_tag_form = QuestionTagForm()
    
    return render_to_response("quanda/tags_admin.html", {
        'tags': QuestionTag.objects.all(),
        'new_tag_form': new_tag_form,
        }, context_instance=RequestContext(request))
    
@login_required # TODO: staff only
def delete_tag(request, tag_id):
    tag = get_object_or_404(QuestionTag, pk=tag_id)
    tag.delete()
    return HttpResponseRedirect(reverse('quanda_tags_admin'))
    
def profile(request, username):
    
    user = get_object_or_404(User, username=username)
    profile = Profile.objects.get_or_create(user=user)[0]

    if request.method == 'POST':
        if not request.user.is_staff: raise Http404
        rep_form = RepForm(request.POST)
        if rep_form.is_valid():
            profile.reputation = rep_form.cleaned_data['base_rep']
            profile.save()
            return HttpResponseRedirect(reverse('quanda_public_profile', args=[username]))
    else:
        rep_form = RepForm(initial={'base_rep': profile.reputation})
    
    return render_to_response("quanda/profile.html", {
        'rep_form': rep_form,
        'questions': Question.objects.filter(author__username=username).order_by('-posted'),
        'profile': profile,
        }, context_instance=RequestContext(request))

def lists(request):
    if request.method == 'POST':
        form = QuestionListForm(request.POST)
        if form.is_valid():
            list = form.save()
            return HttpResponseRedirect(reverse('quanda_lists'))
    else:
        form = QuestionListForm()
    return render_to_response("quanda/lists.html", {
        'form': form,
        'lists': QuestionList.objects.all(),
    }, context_instance=RequestContext(request))
    
def list_details(request, list_id):
    list = QuestionList.objects.get(pk=list_id)

    if request.method == "POST":
        edit_form = QuestionListForm(request.POST, instance=list)
        if edit_form.is_valid():
            list = edit_form.save()
            return HttpResponseRedirect(reverse('quanda_list_details', args=[list.id]))
    else:
        edit_form = QuestionListForm(instance=list)
        
    #QuestionListOrder.objects.filter(question_list=list)
        
    return render_to_response("quanda/list_details.html", {
        'list': list,
        'edit_form': edit_form,
        'order_form': QuestionListOrderForm(),
        'questions': QuestionListOrder.objects.filter(question_list=list),
    }, context_instance=RequestContext(request))
    return HttpResponse('details')