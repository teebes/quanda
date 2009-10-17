from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.contrib.syndication.feeds import Feed

from quanda.models import Question, Answer

class RssQuestions(Feed):
    title_template = 'quanda-feeds/question-title.html'
    description_template = 'quanda-feeds/question-description.html'
    
    def __init__(self, *args, **kwargs):
        super(RssQuestions, self).__init__(*args, **kwargs)
        self.site_name = Site.objects.get_current().name
    
    def title(self):
        return u"Latest %s questions" % self.site_name
    
    def description(self):
        return u"Latest questions posted on %s" % self.site_name
    
    def link(self):
        return reverse('quanda_index')
    
    def items(self):
        return Question.objects.order_by("-posted")[:20]
            
    def item_link(self, item):
        return item.get_absolute_url()

class RssAnswers(Feed):
    title_template = "quanda-feeds/answer-title.html"
    description_template = "quanda-feeds/answer-description.html"

    def get_object(self, bits):
        if len(bits) != 1: raise ObjectDoesNotExist
        return Question.objects.get(pk=bits[0])

    def description(self, obj):
        return u"Latest answers to question %s" % obj.question_text

    def title(self, obj):
        return u"Answers to %s" % (obj.title)
        return u"Answer by %s to %s" % (obj.author.username, obj.title)

    def link(self):
        return reverse('quanda_index')

    def items(self, obj):
        return Answer.objects.filter(question=obj).order_by('-posted')

    #def item_link(self, answer):
    #    return 'http://abc'
    #    return u"%s#%s" % (
    #        answer.question.get_absolute_url(),
    #        answer.id
    #    )