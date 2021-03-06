from geoalchemy2.elements import WKTElement

from fwas import db
from fwas.models import Alert, User


def create_seeds():
    admin = User(
        email="levi.malott@gmail.com",
        username="levi_admin",
        password="secret12345",
        phone="123-456-7890",
        role="admin",
        active=True,
    )
    user = User(
        email="levi.malott+2@gmail.com",
        username="levi",
        password="secret12345",
        phone="123-456-7890",
    )

    lat = 38.6247
    lon = -90.1854
    point = WKTElement(f"POINT({lon} {lat})", srid=4326)
    alert = Alert(
        user=user,
        name="St. Louis Arch",
        latitude=lat,
        longitude=lon,
        geom=point,
        radius=20000.0,
        timezone="America/Chicago",
        expires_at=None,
        temperature_limit=0.0,  # celcius
        precipitation_limit=5,  # inches
        relative_humidity_limit=80.0,  # percent
        wind_limit=1.0,  # meters / second
    )

    alert2 = Alert(
        user=user,
        name="St. Louis Ballpark",
        latitude=lat,
        longitude=lon,
        geom=point,
        radius=50000.0,
        timezone="America/Chicago",
        expires_at=None,
        temperature_limit=20.0,  # celcius
        precipitation_limit=1.0,  # inches
        relative_humidity_limit=90.0,  # percent
        wind_limit=1.0,  # meters / second
    )
    alert2.subscribers.append(admin)

    db.session.add_all([admin, user, alert, alert2])
    db.session.commit()
