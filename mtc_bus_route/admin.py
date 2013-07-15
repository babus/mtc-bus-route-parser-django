from django.contrib import admin
from mtc_bus_route.models import *


class BusStopAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'wiki_link')
    list_display_links = ('id', 'name')
    ordering = ('name', 'id')
    search_fields = ('name',)


class BusRouteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'start_stop', 'end_stop', 'bus_type_code', 'is_high_frequency',
                    'is_low_frequency', 'is_night_service')
    list_display_links = ('id', 'name')
    list_filter = ('bus_type_code', 'is_high_frequency', 'is_low_frequency', 'is_night_service')
    ordering = ('name', 'id')
    search_fields = ('start_stop__name', 'end_stop__name')


class BusRoutePathAdmin(admin.ModelAdmin):
    list_display = ('id', 'route', 'stop', 'order')
    list_display_links = ('id',)
    ordering = ('stop', 'id')
    list_filter = ('route', 'stop')
    search_fields = ('route__name', 'stop__name')

admin.site.register(BusRoute, BusRouteAdmin)
admin.site.register(BusRoutePath, BusRoutePathAdmin)
admin.site.register(BusStop, BusStopAdmin)
