from django.core.paginator import Paginator
from django.db.models import Count, Max, Prefetch, Q
from django.shortcuts import get_object_or_404, render

from .forms import ProviderSearchForm
from .models import DataSource, ExcludedParty, ExclusionRecord, Identifier, ImportLog


def search(request):
    form = ProviderSearchForm(request.GET or None)
    totals = {
        "parties": ExcludedParty.objects.count(),
        "identifiers": Identifier.objects.count(),
        "sources": DataSource.objects.count(),
        "latest_import": ImportLog.objects.aggregate(latest=Max("imported_at"))["latest"],
    }
    return render(request, "exclusions/search.html", {"form": form, "totals": totals})


def results(request):
    form = ProviderSearchForm(request.GET)
    parties = ExcludedParty.objects.prefetch_related(
        "identifiers",
        Prefetch(
            "exclusion_records",
            queryset=ExclusionRecord.objects.select_related("data_source").order_by("-exclusion_date"),
        ),
    )

    if form.is_valid():
        data = form.cleaned_data
        q = data.get("q")
        if q:
            name_query = (
                Q(first_name__icontains=q)
                | Q(middle_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(business_name__icontains=q)
                | Q(identifiers__identifier_value__icontains=q)
            )
            parts = q.split()
            if len(parts) >= 2:
                name_query |= Q(first_name__icontains=parts[0], last_name__icontains=parts[-1])
            parties = parties.filter(name_query)

        if data.get("party_type"):
            parties = parties.filter(party_type=data["party_type"])
        if data.get("state"):
            parties = parties.filter(state__iexact=data["state"])
        if data.get("city"):
            parties = parties.filter(city__icontains=data["city"])
        if data.get("zip_code"):
            parties = parties.filter(zip_code__startswith=data["zip_code"])
        if data.get("source"):
            parties = parties.filter(exclusion_records__data_source=data["source"])
        if data.get("status"):
            parties = parties.filter(exclusion_records__status__iexact=data["status"])
        if data.get("exclusion_type"):
            parties = parties.filter(exclusion_records__exclusion_type__iexact=data["exclusion_type"])
        if data.get("date_from"):
            parties = parties.filter(exclusion_records__exclusion_date__gte=data["date_from"])
        if data.get("date_to"):
            parties = parties.filter(exclusion_records__exclusion_date__lte=data["date_to"])

    parties = parties.distinct()
    paginator = Paginator(parties, 25)
    page = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "exclusions/results.html",
        {"form": form, "page": page, "result_count": paginator.count},
    )


def detail(request, party_id):
    party = get_object_or_404(
        ExcludedParty.objects.prefetch_related(
            "identifiers",
            Prefetch(
                "exclusion_records",
                queryset=ExclusionRecord.objects.select_related("data_source", "import_log").order_by("-exclusion_date"),
            ),
        ),
        party_id=party_id,
    )
    return render(request, "exclusions/detail.html", {"party": party})


def sources(request):
    data_sources = DataSource.objects.annotate(record_count=Count("exclusionrecord")).order_by("source_name")
    import_logs = ImportLog.objects.select_related("data_source").order_by("-imported_at")
    return render(request, "exclusions/sources.html", {"data_sources": data_sources, "import_logs": import_logs})
