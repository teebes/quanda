import datetime
import hashlib
import random

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify

def get_posted_date(obj):
    delta = datetime.datetime.now() - obj.posted
    if delta.days < 364:
        format = "%b %d"
    else:
        format = "%b %d %y"
    return u"%s" % obj.posted.strftime(format)

class Profile(models.Model):
    """A user using the Quanda system. This can be an anonymous user."""
    user = models.OneToOneField(User)
    
    # Since rep is calculated dynamically, this represents reputation awarded
    # outside the regular rep process (say by an admin)
    reputation = models.IntegerField(default=0)
    website = models.CharField(max_length=140, blank=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=140, blank=True)
    
    def __unicode__(self):
        return u"quanda user %s" % self.user

class QuestionManager(models.Manager): pass

class Question(models.Model):
    title = models.CharField(max_length=140)
    question_text = models.TextField(blank=True)
    
    posted = models.DateTimeField(default=datetime.datetime.now)
    last_modified = models.DateTimeField(default=datetime.datetime.now)
    author = models.ForeignKey(User, blank=True, null=True)
    
    get_posted_date = get_posted_date
    objects = QuestionManager()
    
    def get_score(self):
        score = 0
        for question_vote in QuestionVote.objects.filter(question=self):
            score += question_vote.score
        return score
    
    def get_absolute_url(self):
        return "%s%s" % (
            reverse("quanda_question_read", args=[self.id]),
            slugify(self.title))
        
    def get_ref(self):
        """returns a ready-for-html string with the question score, title and
        link"""
        
        return u"%s &bull; <a href='%s'>%s</a>" % (
                self.get_score(),
                #reverse('quanda_question_read', args=[self.id]),
                self.get_absolute_url(),
                self.title,
            )
        
        
    def __unicode__(self):
        return u"%s, %s" % (self.id, self.title)

class QuestionVote(models.Model):
    user = models.ForeignKey(User)
    question = models.ForeignKey(Question, related_name='questionvotes')
    score = models.IntegerField(default=0)
    
class QuestionTag(models.Model):
    title = models.CharField(max_length=140, unique=True)
    questions = models.ManyToManyField(Question, related_name='tags')
    created = models.DateTimeField(default=datetime.datetime.now())
    
    def __unicode__(self): return u"%s" % self.title
    
    class Meta:
        ordering = ('title',)

class QuestionList(models.Model):
    title = models.CharField(max_length=140, unique=True)
    questions = models.ManyToManyField(Question, through='QuestionListOrder', related_name='lists')
    created = models.DateTimeField(default=datetime.datetime.now())

class QuestionListOrder(models.Model):
    question = models.ForeignKey(Question)
    question_list = models.ForeignKey(QuestionList)
    order = models.IntegerField(blank=False)

class RepRule(models.Model):
    # The axe hangs over this model, still need to think through rep
    # permissions / thresholds
    title = models.CharField(max_length=140, unique=True)
    threshold = models.IntegerField(default=0)
    giver_reward = models.IntegerField(default=0)
    receiver_reward = models.IntegerField(default=0)

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers')    
    answer_text = models.TextField()

    posted = models.DateTimeField(default=datetime.datetime.now)
    last_modified = models.DateTimeField(default=datetime.datetime.now)
    author = models.ForeignKey(User)
    user_chosen = models.BooleanField(default=False)
    
    get_posted_date = get_posted_date
    
    def __init__(self, *args, **kwargs):
        super(Answer, self).__init__(*args, **kwargs)
        self.user_prev_vote = 0
    
    def get_score(self):
        score = 0
        for answer_vote in AnswerVote.objects.filter(answer=self):
            score += answer_vote.score
        return score

    def __unicode__(self):
        return u"answer %s: %s" % (self.id, self.answer_text)

class AnswerVote(models.Model):
    user = models.ForeignKey(User)
    answer = models.ForeignKey(Answer, related_name='answervotes')
    score = models.IntegerField(default=0)
