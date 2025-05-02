AQI_BREAKPOINTS = {
    "co": [
        (4.4, 50, 0),
        (9.4, 100, 51),
        (12.4, 150, 101),
        (15.4, 200, 151),
        (30.4, 300, 201),
        (40.4, 400, 301),
        (50.4, 500, 401),
    ],
    "no2": [
        (40, 50, 0),
        (90, 100, 51),
        (120, 150, 101),
        (230, 200, 151),
        (340, 300, 201),
        (1000, 400, 301),
    ],
    "o3": [
        (50, 50, 0),
        (100, 100, 51),
        (130, 150, 101),
        (240, 200, 151),
        (380, 300, 201),
        (800, 400, 301),
    ],
    "pm2_5": [
        (10, 50, 0),
        (20, 100, 51),
        (25, 150, 101),
        (50, 200, 151),
        (75, 300, 201),
        (800, 400, 301),
    ],
    "pm10": [
        (20, 50, 0),
        (40, 100, 51),
        (50, 150, 101),
        (100, 200, 151),
        (150, 300, 201),
        (1200, 400, 301),
    ],
    "so2": [
        (100, 50, 0),
        (200, 100, 51),
        (350, 150, 101),
        (500, 200, 151),
        (750, 300, 201),
        (1250, 400, 301),
    ],
}


def calculate_aqi(*args) -> int:
    return max(args)


def calculate_index(pollutant: str, value: float) -> int:
    for aqi_breakpoint in AQI_BREAKPOINTS[pollutant]:
        if value <= aqi_breakpoint[0]:
            return to_aqi(
                aqi_breakpoint[1], aqi_breakpoint[2], aqi_breakpoint[0], 0, value
            )
    return 0


def to_aqi(i_high: int, i_low: int, c_high: float, c_low: float, c: float) -> int:
    return int((i_high - i_low) * (c - c_low) / (c_high - c_low) + i_low)
