from django.shortcuts import render

KG_APPS = ["kg_train", "kg_test", "kg_viz"]

class IndexView(generic.ListView):
    template_name = "kg_admin/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """ Return the last five published questions."""
        # return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]
        return KG_APPS
