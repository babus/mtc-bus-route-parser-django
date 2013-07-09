from django.db.models import get_models, get_app
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered


ignore_list = []


def autoregister(*app_list):
    for app_name in app_list:
        app_models = get_app(app_name)
        for model in get_models(app_models):
            if model not in ignore_list:
                try:
                    admin.site.register(model)
                except AlreadyRegistered:
                    pass

autoregister("mtc_bus_route")
