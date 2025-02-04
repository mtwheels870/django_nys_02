from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from django_tables2 import SingleTableView

from .models import PrdgyDataset, PrdgyLink
from .tables import DatasetTable

class DatasetIndexView(SingleTableView):
    model = PrdgyDataset
    table_class = DatasetTable
    template_name = "kg_train/dataset_detail.html"
    table_pagination = {
        "per_page": 10
    }

    def get_queryset(self):
        return PrdgyDataset.objects.all()

    def post(self, request, *args, **kwargs):
        selected_pks = request.POST.getlist('selection')
        num_selected = len(selected_pks)
        if num_selected  == 0:
            print(f"DDV.post(), no selected rows")
            return redirect(request.path)
        elif num_selected > 1:
            print(f"DDV.post(), >1 selected rows")
            return redirect(request.path)
        else:
            # Check which button we're in: edit or label
            dataset_id = selected_pks[0]
            dataset = get_object_or_404(PrdgyDataset, pk=dataset_id)
            print(f"DDV.post(), selected dataset: {dataset}")
            return HttpResponseRedirect(reverse("app_kg_train:index"))

class DatasetDetailView(SingleTableView):
    model = PrdgyLink
    table_class = LinkTable
    template_name = "kg_train/folder_detail.html"
    table_pagination = {
        "per_page": 10
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dataset_id'] = self.folder_id
        # print(f"TFDW.get_context_data(), folder_id = {self.folder_id}")
        return context

    def get_queryset(self):
        self.dataset_id = self.kwargs.get('dataset_id')
        return PrdgyLink.objects.filter(dataset_id=self.dataset_id)

    def post(self, request, *args, **kwargs):
        dataset_id = kwargs["dataset_id"]
        selected_pks = request.POST.getlist('selection')
        num_selected = len(selected_pks)
        if num_selected  == 0:
            print(f"DDV.post(), no selected rows")
            return redirect(request.path)
        elif num_selected > 1:
            print(f"DDV.post(), >1 selected rows")
            return redirect(request.path)
        else:
            # Check which button we're in: edit or label
            link_id = selected_pks[0]
            print(f"DDV.post(), link {link_id} selected")
            return HttpResponseRedirect(reverse("app_kg_viz:index"))
