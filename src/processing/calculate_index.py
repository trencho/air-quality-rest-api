def calculate_aqi(*args) -> int:
    return max(args)


def calculate_co_index(co: float) -> int:
    if co <= 4.4:
        return to_aqi(50, 0, 4.4, 0, co)
    elif 4.4 < co <= 9.4:
        return to_aqi(100, 51, 9.4, 4.5, co)
    elif 9.4 < co <= 12.4:
        return to_aqi(150, 101, 12.4, 9.5, co)
    elif 12.4 < co <= 15.4:
        return to_aqi(200, 151, 15.4, 12.5, co)
    elif 15.4 < co <= 30.4:
        return to_aqi(300, 201, 30.4, 15.5, co)
    elif 30.4 < co <= 40.4:
        return to_aqi(400, 301, 40.4, 30.5, co)
    elif 40.4 < co <= 50.4:
        return to_aqi(500, 401, 50.4, 40.5, co)

    return 0


def calculate_no2_index(no2: float) -> int:
    if no2 <= 40:
        return to_aqi(50, 0, 40, 0, no2)
    elif 40 < no2 <= 90:
        return to_aqi(100, 51, 90, 41, no2)
    elif 90 < no2 <= 120:
        return to_aqi(150, 101, 120, 91, no2)
    elif 120 < no2 <= 230:
        return to_aqi(200, 151, 230, 121, no2)
    elif 230 < no2 <= 340:
        return to_aqi(300, 201, 340, 231, no2)
    elif 340 < no2 <= 1000:
        return to_aqi(400, 301, 1000, 341, no2)

    return 0


def calculate_o3_index(o3: float) -> int:
    if o3 <= 50:
        return to_aqi(50, 0, 50, 0, o3)
    elif 50 < o3 <= 100:
        return to_aqi(100, 51, 100, 51, o3)
    elif 100 < o3 <= 130:
        return to_aqi(150, 101, 130, 101, o3)
    elif 130 < o3 <= 240:
        return to_aqi(200, 151, 240, 131, o3)
    elif 240 < o3 <= 380:
        return to_aqi(300, 201, 380, 241, o3)
    elif 380 < o3 <= 800:
        return to_aqi(400, 301, 800, 381, o3)

    return 0


def calculate_pm2_5_index(pm2_5: float) -> int:
    if pm2_5 <= 10:
        return to_aqi(50, 0, 10, 0, pm2_5)
    elif 10 < pm2_5 <= 20:
        return to_aqi(100, 51, 20, 11, pm2_5)
    elif 20 < pm2_5 <= 25:
        return to_aqi(150, 101, 25, 21, pm2_5)
    elif 25 < pm2_5 <= 50:
        return to_aqi(200, 151, 50, 26, pm2_5)
    elif 50 < pm2_5 <= 75:
        return to_aqi(300, 201, 75, 51, pm2_5)
    elif 75 < pm2_5 <= 800:
        return to_aqi(400, 301, 800, 76, pm2_5)

    return 0


def calculate_pm10_index(pm10: float) -> int:
    if pm10 <= 20:
        return to_aqi(50, 0, 20, 0, pm10)
    elif 20 < pm10 <= 40:
        return to_aqi(100, 51, 40, 21, pm10)
    elif 40 < pm10 <= 50:
        return to_aqi(150, 101, 50, 41, pm10)
    elif 50 < pm10 <= 100:
        return to_aqi(200, 151, 100, 51, pm10)
    elif 100 < pm10 <= 150:
        return to_aqi(300, 201, 150, 101, pm10)
    elif 150 < pm10 <= 1200:
        return to_aqi(400, 301, 1200, 151, pm10)

    return 0


def calculate_so2_index(so2: float) -> int:
    if so2 <= 100:
        return to_aqi(50, 0, 100, 0, so2)
    elif 100 < so2 <= 200:
        return to_aqi(100, 51, 200, 101, so2)
    elif 200 < so2 <= 350:
        return to_aqi(150, 101, 350, 201, so2)
    elif 350 < so2 <= 500:
        return to_aqi(200, 151, 500, 351, so2)
    elif 500 < so2 <= 750:
        return to_aqi(300, 201, 750, 501, so2)
    elif 750 < so2 <= 1250:
        return to_aqi(400, 301, 1250, 751, so2)

    return 0


def to_aqi(i_high: int, i_low: int, c_high: float, c_low: float, c: float) -> int:
    return int((i_high - i_low) * (c - c_low) / (c_high - c_low) + i_low)
