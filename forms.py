import datetime

from django import forms
from django.contrib.auth.models import User

from quanda.models import Question, QuestionList, QuestionListOrder, QuestionTag, Answer

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
            try:
                question.author = User.objects.get(username='anonymous_user')
            except User.DoesNotExist: # this should only ever happen once
                # TODO: this is poorly placed. Right now it assumes that
                # anyone using quanda will create a question as anonymous
                # to create this user. Someone could answer a question before
                # any anon ask a question
                anonymous_user = User(username='anonymous_user')
                anonymous_user.save()
                question.author = anonymous_user
        
        question.last_modified = datetime.datetime.now()
        question.save()

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
        answer.last_modified = datetime.datetime.now()
        answer.save()
        return answer
    
    def clean(self):
        if self.author.is_authenticated():
            if Answer.objects.filter(question=self.question, author=self.author):
                raise forms.ValidationError("You've already answered this question.")
        return self.cleaned_data
    
class RepForm(forms.Form):
    base_rep = forms.IntegerField()
    #username = forms.CharField(max_length=140, widget=forms.HiddenInput, required=True)

class QuestionListForm(forms.ModelForm):
    class Meta:
        model = QuestionList
        exclude = ['created', 'questions']
        
class QuestionListOrderForm(forms.ModelForm):
    class Meta:
        model = QuestionListOrder

    

    