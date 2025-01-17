from django.shortcuts import render
from django.views import generic

class KgApp:
    def __init__(self, name, url):
        self.name = name;
        self.url = url;

train = KgApp("kg_train", "../../index.html")
test = KgApp("kg_test", "../../test.html")
viz = KgApp("kg_viz", "../../viz.html")

KG_APPS = [train, test, viz]

class IndexView(generic.ListView):
    template_name = "kg_admin/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """ Return the last five published questions."""
        # return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]
        return KG_APPS
