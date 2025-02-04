from django_tables2 import SingleTableView

from .models import TextFileStatus, TextFile, TextFolder
from .forms import UploadFolderForm
from .tables import TextFileTable
from .tasks import prodigy_start

class DatasetDetailView(SingleTableView):
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
