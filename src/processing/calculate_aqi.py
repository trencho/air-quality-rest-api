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

    if no2 <= 40:
        no2_aqi = no2 * 50 / 40
    elif 40 < no2 <= 90:
        no2_aqi = (no2 - 41) * (100 - 51) / (90 - 41) + 51
    elif 90 < no2 <= 120:
        no2_aqi = (no2 - 91) * (150 - 101) / (120 - 91) + 101
    elif 120 < no2 <= 230:
        no2_aqi = (no2 - 121) * (200 - 151) / (230 - 121) + 151
    elif 230 < no2 <= 340:
        no2_aqi = (no2 - 231) * (300 - 201) / (340 - 231) + 201
    elif 340 < no2 <= 1000:
        no2_aqi = (no2 - 341) * (400 - 301) / (1000 - 341) + 301

    return no2_aqi


def calculate_o3_aqi(o3):
    o3_aqi = 0

    if o3 <= 50:
        o3_aqi = o3 * 50 / 50
    elif 50 < o3 <= 100:
        o3_aqi = (o3 - 51) * (100 - 51) / (100 - 51) + 51
    elif 100 < o3 <= 130:
        o3_aqi = (o3 - 101) * (150 - 101) / (130 - 101) + 101
    elif 130 < o3 <= 240:
        o3_aqi = (o3 - 131) * (200 - 151) / (240 - 131) + 151
    elif 240 < o3 <= 380:
        o3_aqi = (o3 - 241) * (300 - 201) / (380 - 241) + 201
    elif 380 < o3 <= 800:
        o3_aqi = (o3 - 381) * (400 - 301) / (800 - 381) + 301

    return o3_aqi


def calculate_pm25_aqi(pm25):
    pm25_aqi = 0

    if pm25 <= 10:
        pm25_aqi = pm25 * 50 / 10
    elif 10 < pm25 <= 20:
        pm25_aqi = (pm25 - 11) * (100 - 51) / (20 - 11) + 51
    elif 20 < pm25 <= 25:
        pm25_aqi = (pm25 - 21) * (150 - 101) / (25 - 21) + 101
    elif 25 < pm25 <= 50:
        pm25_aqi = (pm25 - 26) * (200 - 151) / (50 - 26) + 151
    elif 50 < pm25 <= 75:
        pm25_aqi = (pm25 - 51) * (300 - 201) / (75 - 51) + 201
    elif 75 < pm25 <= 800:
        pm25_aqi = (pm25 - 76) * (400 - 301) / (800 - 76) + 301

    return pm25_aqi


def calculate_pm10_aqi(pm10):
    pm10_aqi = 0

    if pm10 <= 20:
        pm10_aqi = pm10 * 50 / 20
    elif 20 < pm10 <= 40:
        pm10_aqi = (pm10 - 21) * (100 - 51) / (40 - 21) + 51
    elif 40 < pm10 <= 50:
        pm10_aqi = (pm10 - 41) * (150 - 101) / (50 - 41) + 101
    elif 50 < pm10 <= 100:
        pm10_aqi = (pm10 - 51) * (200 - 151) / (100 - 51) + 151
    elif 100 < pm10 <= 150:
        pm10_aqi = (pm10 - 101) * (300 - 201) / (150 - 101) + 201
    elif 150 < pm10 <= 1200:
        pm10_aqi = (pm10 - 151) * (400 - 301) / (1200 - 151) + 301

    return pm10_aqi


def calculate_so2_aqi(so2):
    so2_aqi = 0

    if so2 <= 100:
        so2_aqi = so2 * (50 / 100)
    elif 100 < so2 <= 200:
        so2_aqi = (so2 - 101) * (100 - 51) / (200 - 101) + 51
    elif 200 < so2 <= 350:
        so2_aqi = (so2 - 201) * (100 - 51) / (350 - 201) + 101
    elif 350 < so2 <= 500:
        so2_aqi = (so2 - 351) * (100 - 51) / (500 - 351) + 151
    elif 500 < so2 <= 750:
        so2_aqi = (so2 - 501) * (100 - 51) / (750 - 501) + 201
    elif 750 < so2 <= 1250:
        so2_aqi = (so2 - 751) * (100 - 51) / (1250 - 751) + 301

    return so2_aqi


def calculate_aqi(co_aqi, no2_aqi, o3_aqi, pm25_aqi, pm10_aqi, so2_aqi):
    parameters = []
    parameters.extend([co_aqi, no2_aqi, o3_aqi, pm25_aqi, pm10_aqi, so2_aqi])
    aqi = max(parameters)

    return aqi
