def calculate_co_aqi(co):
    co_aqi = 0

    if co <= 4.4:
        co_aqi = co * 50 / 4.4
    elif 4.4 < co <= 9.4:
        co_aqi = (co - 4.5) * (100 - 51) / (9.4 - 4.5) + 51
    elif 9.4 < co <= 12.4:
        co_aqi = (co - 9.5) * (150 - 101) / (12.4 - 9.5) + 101
    elif 12.4 < co <= 15.4:
        co_aqi = (co - 12.5) * (200 - 151) / (15.4 - 12.5) + 151
    elif 15.4 < co <= 30.4:
        co_aqi = (co - 15.5) * (300 - 201) / (30.4 - 15.5) + 201
    elif 30.4 < co <= 40.4:
        co_aqi = (co - 30.5) * (400 - 301) / (40.4 - 30.5) + 301
    elif 40.4 < co <= 50.4:
        co_aqi = (co - 40.5) * (500 - 401) / (2049 - 1650) + 401

    return co_aqi


def calculate_no2_aqi(no2):
    no2_aqi = 0

    if no2 <= 53:
        no2_aqi = no2 * 50 / 53
    elif 53 < no2 <= 100:
        no2_aqi = (no2 - 54) * (100 - 51) / (100 - 54) + 51
    elif 100 < no2 <= 360:
        no2_aqi = (no2 - 101) * (150 - 101) / (360 - 101) + 101
    elif 360 < no2 <= 649:
        no2_aqi = (no2 - 361) * (200 - 151) / (649 - 361) + 151
    elif 649 < no2 <= 1249:
        no2_aqi = (no2 - 650) * (300 - 201) / (1249 - 650) + 201
    elif 1249 < no2 <= 1649:
        no2_aqi = (no2 - 1250) * (400 - 301) / (1649 - 1250) + 301
    elif 1649 < no2 <= 2049:
        no2_aqi = (no2 - 1650) * (500 - 401) / (2049 - 1650) + 401

    return no2_aqi


def calculate_o3_aqi(o3):
    o3_aqi = 0

    if 124 < o3 <= 164:
        o3_aqi = (o3 - 125) * (150 - 101) / (164 - 125) + 101
    elif 164 < o3 <= 204:
        o3_aqi = (o3 - 165) * (200 - 151) / (204 - 165) + 151
    elif 204 < o3 <= 404:
        o3_aqi = (o3 - 205) * (300 - 201) / (404 - 205) + 201
    elif 404 < o3 <= 504:
        o3_aqi = (o3 - 405) * (400 - 301) / (504 - 405) + 301
    elif 504 < o3 <= 604:
        o3_aqi = (o3 - 505) * (500 - 401) / (604 - 505) + 401

    return o3_aqi


def calculate_pm25_aqi(pm25):
    pm25_aqi = 0

    if pm25 <= 12:
        pm25_aqi = pm25 * 50 / 12
    elif 12 < pm25 <= 35.4:
        pm25_aqi = (pm25 - 12) * (100 - 51) / (35.4 - 12.1) + 51
    elif 35.4 < pm25 <= 55.4:
        pm25_aqi = (pm25 - 35.5) * (150 - 101) / (55.4 - 35.5) + 101
    elif 55.4 < pm25 <= 150.4:
        pm25_aqi = (pm25 - 55.5) * (200 - 151) / (150.4 - 55.5) + 151
    elif 150.4 < pm25 <= 250.4:
        pm25_aqi = (pm25 - 150.5) * (300 - 201) / (250.4 - 150.5) + 201
    elif 250.4 < pm25 <= 350.4:
        pm25_aqi = (pm25 - 250.5) * (400 - 301) / (350.4 - 250.5) + 301
    elif 350.4 < pm25 <= 500.4:
        pm25_aqi = (pm25 - 350.5) * (500 - 401) / (500.4 - 350.5) + 401

    return pm25_aqi


def calculate_pm10_aqi(pm10):
    pm10_aqi = 0

    if pm10 <= 54:
        pm10_aqi = pm10 * 50 / 54
    elif 54 < pm10 <= 154:
        pm10_aqi = (pm10 - 55) * (100 - 51) / (154 - 55) + 51
    elif 154 < pm10 <= 254:
        pm10_aqi = (pm10 - 155) * (150 - 101) / (254 - 155) + 101
    elif 254 < pm10 <= 354:
        pm10_aqi = (pm10 - 255) * (200 - 151) / (354 - 255) + 151
    elif 354 < pm10 <= 424:
        pm10_aqi = (pm10 - 355) * (300 - 201) / (424 - 355) + 201
    elif 424 < pm10 <= 504:
        pm10_aqi = (pm10 - 425) * (400 - 301) / (504 - 425) + 301
    elif 504 < pm10 <= 604:
        pm10_aqi = (pm10 - 505) * (500 - 401) / (604 - 505) + 401

    return pm10_aqi


def calculate_so2_aqi(so2):
    so2_aqi = 0

    if so2 <= 35:
        so2_aqi = so2 * (50 / 35)
    elif 35 < so2 <= 75:
        so2_aqi = (so2 - 36) * (100 - 51) / (75 - 36) + 51
    elif 75 < so2 <= 185:
        so2_aqi = (so2 - 76) * (100 - 51) / (185 - 76) + 51
    elif 185 < so2 <= 304:
        so2_aqi = (so2 - 186) * (100 - 51) / (304 - 186) + 51
    elif 304 < so2 <= 604:
        so2_aqi = (so2 - 305) * (100 - 51) / (604 - 305) + 51
    elif 604 < so2 <= 804:
        so2_aqi = (so2 - 605) * (100 - 51) / (804 - 605) + 51
    elif 804 < so2 <= 1004:
        so2_aqi = (so2 - 805) * (100 - 51) / (1004 - 805) + 51

    return so2_aqi


def calculate_aqi(co_aqi, no2_aqi, o3_aqi, pm25_aqi, pm10_aqi, so2_aqi):
    parameters = []
    parameters.extend([co_aqi, no2_aqi, o3_aqi, pm25_aqi, pm10_aqi, so2_aqi])
    aqi = max(parameters)

    return aqi
