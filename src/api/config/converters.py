from enum import Enum, unique

from flask import Flask
from werkzeug.routing import BaseConverter, ValidationError


@unique
class ErrorType(str, Enum):
    MEAN_ABSOLUTE_ERROR = "mae"
    MEAN_ABSOLUTE_PERCENTAGE_ERROR = "mape"
    MEAN_SQUARED_ERROR = "mse"
    ROOT_MEAN_SQUARED_ERROR = "rmse"


@unique
class PollutantType(str, Enum):
    AQI = "aqi"
    CO = "co"
    NH3 = "nh3"
    NO = "no"
    NO2 = "no2"
    O3 = "o3"
    PM2_5 = "pm2_5"
    PM10 = "pm10"
    SO2 = "so2"


class EnumConverter(BaseConverter):
    enum_class = None

    def to_python(self, value):
        try:
            return self.enum_class(value)
        except ValueError as err:
            raise ValidationError(err)

    def to_url(self, obj):
        return obj.value


class ErrorTypeConverter(EnumConverter):
    enum_class = ErrorType


class PollutantTypeConverter(EnumConverter):
    enum_class = PollutantType


def configure_converters(app: Flask) -> None:
    app.url_map.converters.update(error_type=ErrorTypeConverter)
    app.url_map.converters.update(pollutant_type=PollutantTypeConverter)
