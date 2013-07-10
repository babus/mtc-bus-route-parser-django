"""
"""
import os
import threading
import time
from sys import stdout
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.exceptions import MultipleObjectsReturned
from bs4 import BeautifulSoup
from mtc_bus_route.models import *


class Command(BaseCommand):
    """
    Parse and Sync the routes with database.
    This custom manage command can be issued via manage.py.
    """
    def __init__(self):
        super(Command, self).__init__()
        self.new_route_count = 0
        self.updated_route_count = 0
        self.new_stop_count = 0
        self.updated_stop_count = 0

    def handle(self, *args, **options):
        """
        Entry point for the command execution
        """
        self.print_log("Reading file..")
        current_dir = os.path.dirname(os.path.realpath(__file__))
        try:
            fh = open(os.path.join(current_dir, "routes.html"), "r")

        except IOError as e:
            self.print_log(e)
            self.print_log(
                "File not found: 'routes.html' in %s" % (current_dir))
        else:
            t = threading.Thread(target=self.parse_sync_routes, args=(fh,))
            t.start()
            self.print_log("Started syncing..")
            self.print_progress(t)
        return

    def parse_sync_routes(self, fh):
        try:
            bs_html = BeautifulSoup(fh.read(), "html.parser")
            table = bs_html.find("table", {'class': "Table1"})
            for row_num, each_row in enumerate(table.find_all("tr")):
                if row_num == 0:  # skipping the header row
                    continue
                route = None
                for col_num, each_col in enumerate(each_row.find_all("td")):
                    if col_num == 0:  # Route name
                        # Query for route, if one exists, try updating else add a new one.
                        route_name = each_col.text.strip()
                        try:  # to fetch
                            route = BusRoute.objects.get(name__exact=route_name)
                        except BusRoute.DoesNotExist:  # create a new object
                            route = BusRoute(name=route_name)
                        except MultipleObjectsReturned:
                            self.print_log("Exception: Multiple objects returned for route '%s'." % (
                                route_name))
                        if not route:  # No route fetched or created
                            self.print_log("Cannot create route for row no '%d'." % (row_num + 1))
                            break
                        elif not route.id:  # route doesn't have an id, so a new one
                            self.new_route_count += 1
                        else:  # route has an id
                            self.updated_route_count += 1

                        if "Table1_A4" in each_col['class']:
                            route.bus_type_code = "ADEN"
                        elif "Table1_A7" in each_col['class']:
                            route.bus_type_code = "DEN"
                        elif "Table1_A3" in each_col['class']:
                            route.bus_type_code = "EN"
                        elif "Table1_A1" in each_col['class']:
                            route.bus_type_code = "N"
                        else:
                            # A new bus type has been detected, need to update models,
                            # do schemamigration, and sync again.
                            self.print_log("Detected a new bus type code '%s'." % (bus_type_code))

                    if col_num == 1:  # Starting bus stop
                        if each_col.text:
                            start_stop = self.save_update_bus_stop(stop_name=each_col.text.strip(),
                                                                   anchor=each_col.a)
                            if start_stop:
                                route.start_stop = start_stop
                        else:
                            self.print_log("Route '%s' has no starting stop." % (route.name))
                            break

                    if col_num == 2:  # Ending bus stop
                        if each_col.text:
                            end_stop = self.save_update_bus_stop(stop_name=each_col.text.strip(),
                                                                 anchor=each_col.a)
                            if end_stop:
                                route.end_stop = end_stop
                        else:
                            self.print_log("Route '%s' has no ending stop." % (route.name))
                            break

                    if col_num == 3:  # via route
                        if each_col.text:
                            route.save()
                            path_list = [x.strip() for x in each_col.text.split(',')]
                            path_anchor = zip(path_list, each_col.find_all("a"))
                            if not path_anchor:
                                path_anchor = zip(path_list, [])
                            for order, each_stop in enumerate(path_anchor):
                                via_stop = self.save_update_bus_stop(stop_name=each_stop[0],
                                                                     anchor=each_stop[1])
                                if via_stop:
                                    try:
                                        path_stop = BusRoutePath.objects.get(route=route,
                                                                             stop=via_stop)
                                    except BusRoutePath.DoesNotExist:
                                        path_stop = BusRoutePath(route=route, stop=via_stop,
                                                                 order=order)
                                    to_save = False
                                    if path_stop.order != order:
                                        path_stop.order = order
                                        to_save = True
                                    if not path_stop.id or to_save:
                                        path_stop.save()
                                else:
                                    continue
                        else:  # no path, simply continue
                            continue

                    if col_num == 4:  # High frequency
                        if each_col.text == 'x':
                            route.is_high_frequency = True
                        else:
                            route.is_high_frequency = False

                    if col_num == 5:  # Night service
                        if each_col.text == 'x':
                            route.is_night_service = True
                        else:
                            route.is_night_service = False

                    if col_num == 6:  # Low frequency
                        if each_col.text == 'x':
                            route.is_low_frequency = True
                        else:
                            route.is_low_frequency = False
                route.save()
        except Exception as e:
            self.newline_stdout_flush()
            self.print_log("Exception: %s" % e)
        else:
            self.newline_stdout_flush()
            self.print_log("Synced. 100% done!")
            self.print_log("%d new routes added. %d routes updated." % (self.new_route_count,
                                                                        self.updated_route_count))
            self.print_log("%d new stops added. %d stops updated." % (self.new_stop_count,
                                                                      self.updated_stop_count))
        return

    def save_update_bus_stop(self, stop_name=None, anchor=None):
        """
        Fetches the stop or creates one and return the same.
        """
        # Query for stop, if one exists, try updating else add a new one.
        stop = None
        try:  # to fetch
            stop = BusStop.objects.get(name__exact=stop_name)
        except BusStop.DoesNotExist:  # create a new object
            stop = BusStop(name=stop_name)
        except MultipleObjectsReturned:
            self.print_log("Exception: Multiple objects returned for stop '%s'." % (stop_name))
        if stop:
            to_save = False
            if anchor:
                if stop.wiki_link != anchor['href']:
                    stop.wiki_link = anchor['href']
                    to_save = True
            if not stop.id:
                stop.save()
                self.new_stop_count += 1
            elif to_save:
                stop.save()
                self.updated_stop_count += 1
        return stop

    def print_log(self, msg):
        """
        Prints the log.
        """
        stdout.write("%s | %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
        stdout.flush()

    def print_progress(self, thread_obj):
        """
        Prints the progress of sycing.
        """
        stdout.write("%s | Syncing" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        stdout.flush()
        while thread_obj.is_alive():
            stdout.write(".")
            stdout.flush()
            time.sleep(0.75)
        self.newline_stdout_flush()

    def newline_stdout_flush(self):
        stdout.write("\n")
        stdout.flush()
