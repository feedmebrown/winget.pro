from collections import defaultdict
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Package
from .util import load_tenant, return_jsonresponse, parse_jsonrequest


@require_GET
@load_tenant
def index(*_):
    # The sole motivation for this view is that we want to be able to
    # reverse('winget:index') in instructions for setting up the winget source.
    return HttpResponse("Please log in at /admin for instructions.")


@require_GET
@load_tenant
@return_jsonresponse
def information(*_):
    return {
        'SourceIdentifier': 'api.winget.pro',
        'ServerSupportedVersions': ['1.1.0']
    }


@require_POST
@csrf_exempt
@load_tenant
@parse_jsonrequest
@return_jsonresponse
def manifestSearch(_, data, tenant):
    db_query = Q(tenant=tenant)
    if 'Query' in data:
        keyword = data['Query']['KeyWord']
        db_query &= Q(name__icontains=keyword)
    if 'Inclusions' in data:
        inclusions_query = Q()
        for inclusion in data['Inclusions']:
            field = inclusion['PackageMatchField']
            if field == 'PackageName':
                keyword = inclusion['RequestMatch']['KeyWord']
                inclusions_query |= Q(name__icontains=keyword)
            elif field == 'ProductCode':
                keyword = inclusion['RequestMatch']['KeyWord']
                # We don't have a ProductCode. Use the identifier instead.
                inclusions_query |= Q(identifier__icontains=keyword)
            elif field == 'PackageFamilyName':
                keyword = inclusion['RequestMatch']['KeyWord']
                # We don't have family name. Use the name instead.
                inclusions_query |= Q(name__icontains=keyword)
        db_query &= inclusions_query
    return [
        {
            'PackageIdentifier': package.identifier,
            'PackageName': package.name,
            'Publisher': package.publisher,
            'Versions': [
                {'PackageVersion': version}
                for version in set(
                    package.installer_set.values_list('version', flat=True)
                )
            ]
        }
        for package in Package.objects.filter(db_query)
    ]


@require_GET
@load_tenant
@return_jsonresponse
def packageManifests(request, tenant, identifier):
    package = get_object_or_404(Package, tenant=tenant, identifier=identifier)
    versions = defaultdict(list)
    for installer in package.installer_set.all():
        local_deps = []
        for local_dep in installer.localdependency_set.all():
            local_dep_dict = {
                'PackageIdentifier': local_dep.installer.package.identifier
            }
            if local_dep.minimum_version:
                local_dep_dict['MinimumVersion'] = local_dep.minimum_version
            local_deps.append(local_dep_dict)
        for scope in installer.scopes:
            versions[installer.version].append(
                {
                    'Architecture': installer.architecture,
                    'InstallerType': installer.type,
                    'InstallerUrl':
                        request.build_absolute_uri(installer.file.url),
                    'InstallerSha256': installer.sha256,
                    'Scope': scope,
                    'Dependencies': {
                        'PackageDependencies': local_deps
                    }
                }
            )
    return {
        'PackageIdentifier': package.identifier,
        'Versions': [
            {
                'PackageVersion': version,
                'DefaultLocale': {
                    'PackageLocale': 'en-us',
                    'Publisher': package.publisher,
                    'PackageName': package.name,
                    'ShortDescription': package.description
                },
                'Installers': installers
            }
            for version, installers in versions.items()
        ]
    }
