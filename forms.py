import datetime

from django import forms
from django.contrib.auth.models import User

from quanda.models import Question, QuestionList, QuestionListOrder, QuestionTag, Answer, Profile
from quanda.utils import strip_js

class QuestionForm(forms.ModelForm):
    
    tags = forms.ModelMultipleChoiceField(queryset=QuestionTag.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)
    
    class Meta:
        model = Question
        exclude = ['author', 'posted', 'last_modified']
        
    def __init__(self, author, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.author = author
        
    def save(self, *args, **kwargs):
        kwargs['commit'] = False
        question = super(QuestionForm, self).save(*args, **kwargs)
        
        if self.author.is_authenticated():
            question.author = self.author
        else:
            question.author = User.objects.get(username='anonymous_user')
        
        question.title = strip_js(question.title)
        question.question_text = strip_js(question.question_text)
        question.last_modified = datetime.datetime.now()
        question.save()

        if self.cleaned_data['tags']:
            question.tags = []
            for tag in self.cleaned_data['tags'].all():
                question.tags.add(tag)
            question.save()

        return question
    
class QuestionTagForm(forms.ModelForm):
    class Meta:
        model = QuestionTag
        fields = ['title']
    
    def save(self, *args, **kwargs):
        tag = super(QuestionTagForm, self).save(*args, **kwargs)
        tag.title = tag.title.lower()
        tag.save()
        return tag

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer_text']
        
    def __init__(self, author, question, *args, **kwargs):
        if kwargs.has_key('edit'):
            self.edit = kwargs['edit']            
            del kwargs['edit']
        super(AnswerForm, self).__init__(*args, **kwargs)
        self.author = author
        self.question = question
        
    def save(self, *args, **kwargs):
        kwargs['commit'] = False
        answer = super(AnswerForm, self).save(*args, **kwargs)

        if self.author.is_authenticated():
            answer.author = self.author
        else:
            answer.author = User.objects.get(username='anonymous_user')
        
        answer.question = self.question
        answer.answer_text = strip_js(answer.answer_text)
        answer.last_modified = datetime.datetime.now()
        answer.save()
        return answer
    
    def clean(self):
        if not hasattr(self,'edit') and self.author.is_authenticated():
            if Answer.objects.filter(question=self.question, author=self.author):
                raise forms.ValidationError("You've already answered this question.")
        return self.cleaned_data
    
class RepForm(forms.Form):
    base_rep = forms.IntegerField()
    #username = forms.CharField(max_length=140, widget=forms.HiddenInput, required=True)

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ['user', 'reputation']
    
    def __init__(self, user, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.user = user
    
    def save(self, *args, **kwargs):
        kwargs['commit'] = False
        profile = super(ProfileForm, self).save(*args, **kwargs)
        profile.bio = strip_js(profile.bio)
        profile.user = self.user
        profile.save()
        return profile

class QuestionListForm(forms.ModelForm):
    class Meta:
        model = QuestionList
        exclude = ['created', 'questions']
        
class QuestionListOrderForm(forms.ModelForm):
    class Meta:
        model = QuestionListOrder
        
class QuestionListAddForm(forms.Form):
    question = forms.IntegerField(required=True, label='Question id')
    
    def __init__(self, list, *args, **kwargs):
        super(QuestionListAddForm, self).__init__(*args, **kwargs)
        self.list = list
        
    def clean_question(self):
        id = self.cleaned_data['question']
        try:
            question = Question.objects.get(pk=id)
        except Question.DoesNotExist:
            raise forms.ValidationError("This question does not exist")
        
        if QuestionListOrder.objects.filter(question_list=self.list, question=question):
            raise forms.ValidationError("This question is already on the list")

        return id

