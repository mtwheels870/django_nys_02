from django.shortcuts import render
from django.views import generic

from .templatetags.navigation import KgApp
#class KgApp:
#    def __init__(self, name, url):
#        self.name = name;
#        self.url = url;

train = KgApp("kg_train", "NOT USED")
test = KgApp("kg_test", "NOT USED")
viz = KgApp("kg_viz", "NOT USED")

KG_APPS = [train, test, viz]

class IndexView(generic.ListView):
    template_name = "kg_admin/index.html"
    context_object_name = "latest_question_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # dictionary = { 'kg_train' : "{% url 'app_kg_admin:index'%}",
        dictionary = { 'kg_train' : "../kg_train/templates/kg_train/index.html",
                'kg_test' : "../../test.html", 
                'kg_viz' : "../../viz.html"} 
        context['kg_apps'] = dictionary
        # pk = self.kwargs.get('pk')  # Or 'product_id' if you customized the parameter name
        # Use pk to access the object or do other operations
        return context

    # Don't think we ever use this (b/c among other reasons, no latest_question_list)
    def get_queryset(self):
        """ Return the last five published questions."""
        # return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]
        return KG_APPS
