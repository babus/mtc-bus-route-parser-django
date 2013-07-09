"""
"""
import os
import threading
import time
from sys import stdout
from datetime import datetime
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup
from mtc_bus_route.models import *


class Command(BaseCommand):
    """
    Parse and Sync the routes with database.
    This custom manage command can be issued via manage.py.
    """

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
            self.print_log("File not found: 'routes.html' in %s" % (current_dir))
        else:
            t = threading.Thread(target=self.parse_sync_routes, args=(fh,))
            t.start()
            self.print_log("Started syncing..")
            self.print_progress(t)
            self.print_log("Synced. 100% done!")
        return

    def parse_sync_routes(self, fh):
        try:
            bs_html = BeautifulSoup(fh.read(), "html.parser")
            table = bs_html.find("table", {'class': "Table1"})
            for row_num, each_row in enumerate(table.find_all("tr")):
                if row_num == 0:
                    continue
                for col_num, each_col in enumerate(each_row.find_all("td")):
                    if col_num == 0:  # Route name
                        # Query for route, if one exists, try updating else add a new one.
                        route, created = BusRoute.objects.get_or_create(name=each_col.text)
                        if each_col['class'] == "Table1_A1":
                            route.bus_type_code = "N"
                        elif each_col['class'] == "Table1_A3":
                            route.bus_type_code = "EN"
                        elif each_col['class'] == "Table1_A4":
                            route.bus_type_code = "ADEN"
                        elif each_col['class'] == "Table1_A7":
                            route.bus_type_code = "DEN"
                        else:
                            pass
                    if col_num == 1:  # Starting bus station
                        pass  # Query for station, if one exists, try updating else add a new one.
                    if col_num == 2:  # Ending bus station
                        pass  # Query for station, if one exists, try updating else add a new one.
                    if col_num == 3:  # via route
                        pass  # Little complex to explain. :P
                    if col_num == 4:  # High frequency
                        if each_col.text != " ":
                            pass
                    if col_num == 5:  # Night service
                        if each_col.text != " ":
                            pass
                    if col_num == 6:  # Low frequency
                        if each_col.text != " ":
                            pass
        except Exception as e:
            stdout.write("\n")
            stdout.flush()
            self.print_log("Exception: %s" % e)
        return

    def print_log(self, msg):
        stdout.write("%s | %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
        stdout.flush()

    def print_progress(self, thread_obj):
        stdout.write("%s | Syncing" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        stdout.flush()
        while thread_obj.is_alive():
            stdout.write(".")
            stdout.flush()
            time.sleep(0.75)
        stdout.write("\n")
        stdout.flush()
