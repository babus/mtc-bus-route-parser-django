from django.db import models


class BusRoute(models.Model):
    """
    Bus route model
    """
    BUS_TYPE_CODE = (
        ("N", "Normal"),
        ("EN", "Express and Normal"),
        ("DEN", "Deluxe, Express and Normal"),
        ("ADEN", "AC Volvo, Deluxe, Express and Normal"),
    )

    name = models.CharField("Name", unique=True, max_length=50)
    start_station = models.ForeignKey("BusStop", related_name="routes_start")
    end_station = models.ForeignKey("BusStop", related_name="routes_end")
    path = models.ManyToManyField("BusStop", through="BusRoutePath")
    bus_type_code = models.CharField("Bus types available", choices=BUS_TYPE_CODE, max_length=255)
    is_high_frequency = models.BooleanField('High Frequency', default=False)
    is_night_service = models.BooleanField('Night Service', default=False)
    is_low_frequency = models.BooleanField('Low Frequency', default=False)


class BusRoutePath(models.Model):
    route = models.ForeignKey("BusRoute")
    stop_name = models.ForeignKey("BusStop")
    order = models.IntegerField("Bus stop order")  # This should start with 0


class BusStop(models.Model):
    name = models.CharField("Name", unique=True, max_length=100)
    wiki_link = models.URLField("Wiki weblink", blank=True)
