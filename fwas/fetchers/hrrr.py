import asyncio
import logging
import os
import shutil
import tempfile
import time
from datetime import datetime, timedelta

import click_log
from invoke import run
from loguru import logger

from fwas import crud
from fwas.database import Database
from fwas.config import SQLALCHEMY_DATABASE_URI
from fwas.fetchers import utils
from fwas.fetchers.base import Fetcher


class HrrrFetcher(Fetcher):
    def __init__(self, db: Database):
        self.tempdir = None
        self.db = db

    async def download(self):
        self.tempdir = tempfile.mkdtemp()
        logger.info(f"tempdir created: {self.tempdir}")
        start_hour = datetime.utcnow().hour - 1

        # TODO (lmalott): create appropriate logic for getting the
        # start_hour up to forecast_hour times (handle transition between
        # days as well).
        tasks = [
            retrieve_hrrr_file(start_hour, forecast_hour, self.tempdir)
            for forecast_hour in range(1, 8)
        ]
        await asyncio.gather(*tasks)

    async def transform(self):
        """Convert each grib2 file into SRID 4326. The latter is suitable
        for storage into PostGIS."""
        logger.info("Entering transform phase")
        for grib in os.listdir(self.tempdir):
            path = os.path.join(self.tempdir, grib)
            output_path = os.path.join(self.tempdir, path.replace(".grib2", ".vrt"))
            output_sql = output_path.replace(".vrt", ".sql")
            logger.info(f"Converting {path} to EPSG:4326 at {output_path}")
            run(f"gdalwarp -t_srs EPSG:4326 {path} {output_path}")
            run(
                f"raster2pgsql -I -M -F -s 4326 -t auto -a {output_path} weather_raster > {output_sql}"
            )
            logger.info(f"Removing {path}")
            os.remove(path)

        logger.info("Leaving transform phase")

    async def save(self):
        """Load each .vrt file from tempdir into PostGIS"""
        db_url = os.getenv("DATABASE_URL")
        sql_files = [
            filename for filename in os.listdir(self.tempdir) if ".sql" in filename
        ]
        raster_files = [
            filename for filename in os.listdir(self.tempdir) if ".vrt" in filename
        ]
        for sql_file in sql_files:
            logger.info(f"Saving {sql_file} to database")
            path = os.path.join(self.tempdir, sql_file)
            run(f"psql {db_url} -f {path}")

        current_datetime = datetime.utcnow()
        current_hour = current_datetime.replace(microsecond=0, second=0, minute=0)
        for raster in raster_files:
            # TODO (lmalott): Augment with forecast information such as
            # the forecast data vs measurement data and forecast hour
            async for weather_raster in crud.get_weather_raster_by_filename(
                self.db, raster
            ):
                simulation_offset = get_simulation_offset_from_filename(
                    weather_raster.filename
                )
                weather_raster.created_at = datetime.utcnow()
                weather_raster.updated_at = weather_raster.created_at
                weather_raster.source = "hrrr"
                weather_raster.forecasted_at = current_hour
                weather_raster.forecast_time = current_hour + timedelta(
                    hours=simulation_offset
                )
                await crud.update_weather_raster(self.db, weather_raster)
            logger.info(f"Saved {raster}")

    async def cleanup(self):
        shutil.rmtree(self.tempdir)


def get_simulation_offset_from_filename(filename):
    """Returns the simulation hour from a HRRR Conus GRIB2 filename.

    Each filename has the simulation hour encoded as a 1-based offset.
    The forecast data for the current hour is at offset '01'.
    To extract the simulation hour, we find that offset and take away one.

    Example:
    >>> get_simulation_offset_from_filename('hrrr.t08z.wrfsfcf02.vrt')
    1

    """
    return int(filename.split(".")[2][-2:]) - 1


async def retrieve_hrrr_file(start_hour: int, forecast_hour: int, directory: str):
    """
    Retrieves an HRRR file by building a URL from start_hour and forecast_hour.
    Retults are stored in directory.
    """
    logger.info(f"Downloading forecast hour {forecast_hour}")
    start = time.time()
    url = build_url(start_hour, forecast_hour)

    output_file = os.path.join(
        directory, url[url.find("file=") + 5 : url.find(".grib2")] + ".grib2"
    )
    logger.info(f"Saving forecast {forecast_hour} data to {output_file}")
    await utils.download(url, output_file)
    end = time.time()
    logger.info(f"Download for {forecast_hour} complete in {end - start} seconds")


def build_url(start_hour: int, forecast_hour: int) -> str:
    """
    Builds the most recent URL for HRRR Data

    Args:
        start_hour: Which hour to retrieve HRRR data from. The day is pulled
                    from calling `utcnow()`.
        forecast_hour: Which hour of forecast data to retrieve.

    Returns:
        str: URL of the HRRR grib file to download.
    """
    # If the start_hour is negative, assume that the most recent HRRR data
    # is from the last hour of yesterday.
    if start_hour == -1:
        start_hour = 23
        day = (datetime.utcnow() - timedelta(days=1)).strftime("%Y%m%d")
    else:
        day = datetime.utcnow().strftime("%Y%m%d")

    base_url = "http://nomads.ncep.noaa.gov/cgi-bin/filter_hrrr_2d.pl"
    source_file = f"?file=hrrr.t{start_hour:02}z.wrfsfcf{forecast_hour:02}.grib2"
    params = """&lev_surface=on&lev_10_m_above_ground=on&lev_2_m_above_ground=on\
&lev_entire_atmosphere=on&var_REFC=on&var_RH=on\
&var_TMP=on&var_PRATE=on&var_LTNG=on&var_WIND=on\
&leftlon=0&rightlon=360&toplat=90\
&bottomlat=-90&dir=%2Fhrrr."""

    url = base_url + source_file + params + day + "%2Fconus"
    return url


def run_now():
    with Database(SQLALCHEMY_DATABASE_URI) as db:
        fetcher = HrrrFetcher(db)
        fetcher.run()
