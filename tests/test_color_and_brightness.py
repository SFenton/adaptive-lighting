import datetime as dt
import zoneinfo

import pytest
from astral import LocationInfo
from astral.location import Location
from homeassistant.components.adaptive_lighting.color_and_brightness import (
    SUN_EVENT_NOON,
    SUN_EVENT_SUNRISE,
    SunEvents,
)

# Create a mock astral_location object
location = Location(LocationInfo())

LAT_LONG_TZS = [
    (52.379189, 4.899431, "Europe/Amsterdam"),
    (32.87336, -117.22743, "US/Pacific"),
    (60, 50, "GMT"),
    (60, 50, "UTC"),
]


@pytest.fixture(params=LAT_LONG_TZS)
def tzinfo_and_location(request):
    lat, long, timezone = request.param
    tzinfo = zoneinfo.ZoneInfo(timezone)
    location = Location(
        LocationInfo(
            name="name",
            region="region",
            timezone=timezone,
            latitude=lat,
            longitude=long,
        ),
    )
    return tzinfo, location


def test_replace_time(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )

    new_time = dt.time(5, 30)
    datetime = dt.datetime(2022, 1, 1)
    replaced_time_utc = sun_events._replace_time(datetime.date(), new_time)
    assert replaced_time_utc.astimezone(tzinfo).time() == new_time


def test_sunrise_without_offset(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location

    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    date = dt.datetime(2022, 1, 1).date()
    result = sun_events.sunrise(date)
    assert result == location.sunrise(date)


def test_sun_position_no_fixed_sunset_and_sunrise(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    date = dt.datetime(2022, 1, 1).date()
    sunset = location.sunset(date)
    position = sun_events.sun_position(sunset)
    assert position == 0
    sunrise = location.sunrise(date)
    position = sun_events.sun_position(sunrise)
    assert position == 0
    noon = location.noon(date)
    position = sun_events.sun_position(noon)
    assert position == 1
    midnight = location.midnight(date)
    position = sun_events.sun_position(midnight)
    assert position == -1


def test_sun_position_fixed_sunset_and_sunrise(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=dt.time(6, 0),
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=dt.time(18, 0),
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    date = dt.datetime(2022, 1, 1).date()
    sunset = sun_events.sunset(date)
    position = sun_events.sun_position(sunset)
    assert position == 0
    sunrise = sun_events.sunrise(date)
    position = sun_events.sun_position(sunrise)
    assert position == 0
    noon, midnight = sun_events.noon_and_midnight(date)
    position = sun_events.sun_position(noon)
    assert position == 1
    position = sun_events.sun_position(midnight)
    assert position == -1


def test_noon_and_midnight(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    date = dt.datetime(2022, 1, 1)
    noon, midnight = sun_events.noon_and_midnight(date)
    assert noon == location.noon(date)
    assert midnight == location.midnight(date)


def test_sun_events(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )

    date = dt.datetime(2022, 1, 1)
    events = sun_events.sun_events(date)
    assert len(events) == 4
    assert (SUN_EVENT_SUNRISE, location.sunrise(date).timestamp()) in events


def test_prev_and_next_events(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    datetime = dt.datetime(2022, 1, 1, 10, 0)
    after_sunrise = sun_events.sunrise(datetime.date()) + dt.timedelta(hours=1)
    prev_event, next_event = sun_events.prev_and_next_events(after_sunrise)
    assert prev_event[0] == SUN_EVENT_SUNRISE
    assert next_event[0] == SUN_EVENT_NOON


def test_closest_event(tzinfo_and_location):
    tzinfo, location = tzinfo_and_location
    sun_events = SunEvents(
        name="test",
        astral_location=location,
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        timezone=tzinfo,
    )
    datetime = dt.datetime(2022, 1, 1, 6, 0)
    sunrise = sun_events.sunrise(datetime.date())
    event_name, ts = sun_events.closest_event(sunrise)
    assert event_name == SUN_EVENT_SUNRISE
    assert ts == location.sunrise(sunrise.date()).timestamp()


def test_brightness_inversion_default_mode(tzinfo_and_location):
    """Test brightness inversion with default brightness mode."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location

    # Create settings without inversion
    settings_normal = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        invert_brightness=False,
        timezone=tzinfo,
    )

    # Create settings with inversion
    settings_inverted = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        invert_brightness=True,
        timezone=tzinfo,
    )

    # Test at noon (sun_position > 0)
    noon_time = settings_normal.sun.noon(dt.date(2022, 6, 21))
    brightness_normal_noon = settings_normal.brightness_pct(noon_time, is_sleep=False)
    brightness_inverted_noon = settings_inverted.brightness_pct(
        noon_time, is_sleep=False
    )

    # Normal: noon should be max_brightness (100)
    assert brightness_normal_noon == 100
    # Inverted: noon should be min_brightness (1)
    assert brightness_inverted_noon == 1

    # Test at midnight (sun_position < 0)
    midnight_time = settings_normal.sun.midnight(dt.date(2022, 6, 21))
    brightness_normal_midnight = settings_normal.brightness_pct(
        midnight_time, is_sleep=False
    )
    brightness_inverted_midnight = settings_inverted.brightness_pct(
        midnight_time, is_sleep=False
    )

    # Normal: midnight should be min_brightness (1)
    assert brightness_normal_midnight == 1
    # Inverted: midnight should be max_brightness (100)
    assert brightness_inverted_midnight == 100


def test_brightness_inversion_linear_mode(tzinfo_and_location):
    """Test brightness inversion with linear brightness mode."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location

    settings_normal = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="linear",
        invert_brightness=False,
        timezone=tzinfo,
    )

    settings_inverted = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="linear",
        invert_brightness=True,
        timezone=tzinfo,
    )

    # Test at sunrise
    sunrise_time = settings_normal.sun.sunrise(dt.date(2022, 6, 21))
    brightness_normal = settings_normal.brightness_pct(sunrise_time, is_sleep=False)
    brightness_inverted = settings_inverted.brightness_pct(
        sunrise_time, is_sleep=False
    )

    # The sum should equal max + min
    assert abs(brightness_normal + brightness_inverted - 101) < 1


def test_brightness_inversion_tanh_mode(tzinfo_and_location):
    """Test brightness inversion with tanh brightness mode."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location

    settings_normal = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="tanh",
        invert_brightness=False,
        timezone=tzinfo,
    )

    settings_inverted = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="tanh",
        invert_brightness=True,
        timezone=tzinfo,
    )

    # Test at sunset
    sunset_time = settings_normal.sun.sunset(dt.date(2022, 6, 21))
    brightness_normal = settings_normal.brightness_pct(sunset_time, is_sleep=False)
    brightness_inverted = settings_inverted.brightness_pct(sunset_time, is_sleep=False)

    # The sum should equal max + min
    assert abs(brightness_normal + brightness_inverted - 101) < 1


def test_brightness_inversion_sleep_mode(tzinfo_and_location):
    """Test that sleep mode overrides inversion."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location

    settings_inverted = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=50,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        invert_brightness=True,
        timezone=tzinfo,
    )

    # Test at noon with sleep mode
    noon_time = settings_inverted.sun.noon(dt.date(2022, 6, 21))
    brightness_sleep = settings_inverted.brightness_pct(noon_time, is_sleep=True)

    # Sleep mode should override inversion
    assert brightness_sleep == 50


def test_brightness_inversion_with_different_ranges(tzinfo_and_location):
    """Test brightness inversion with non-standard min/max brightness."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location

    settings_inverted = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=80,
        max_color_temp=5500,
        min_brightness=20,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        invert_brightness=True,
        timezone=tzinfo,
    )

    # Test at noon (should be inverted to min)
    noon_time = settings_inverted.sun.noon(dt.date(2022, 6, 21))
    brightness_noon = settings_inverted.brightness_pct(noon_time, is_sleep=False)
    assert brightness_noon == 20

    # Test at midnight (should be inverted to max)
    midnight_time = settings_inverted.sun.midnight(dt.date(2022, 6, 21))
    brightness_midnight = settings_inverted.brightness_pct(
        midnight_time, is_sleep=False
    )
    assert brightness_midnight == 80


def test_lux_brightness_at_min(tzinfo_and_location):
    """Test brightness at minimum lux (should be max brightness)."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor="sensor.lux",
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    noon_time = settings.sun.noon(dt.date(2022, 6, 21))
    
    # At or below lux_min, should be max brightness
    brightness_0 = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=0.0)
    assert brightness_0 == 100
    
    # Slightly below min should still be max
    brightness_below = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=-10.0)
    assert brightness_below == 100


def test_lux_brightness_at_max(tzinfo_and_location):
    """Test brightness at maximum lux (should be min brightness)."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor="sensor.lux",
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    noon_time = settings.sun.noon(dt.date(2022, 6, 21))
    
    # At or above lux_max, should be min brightness
    brightness_1000 = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=1000.0)
    assert brightness_1000 == 1
    
    # Above max should still be min
    brightness_above = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=2000.0)
    assert brightness_above == 1


def test_lux_brightness_interpolation(tzinfo_and_location):
    """Test brightness interpolation at midpoint lux."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor="sensor.lux",
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    noon_time = settings.sun.noon(dt.date(2022, 6, 21))
    
    # At midpoint (500 lux), should be midpoint brightness
    brightness_mid = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=500.0)
    expected_mid = (100 + 1) / 2  # 50.5
    assert abs(brightness_mid - expected_mid) < 1.0
    
    # At quarter point (250 lux)
    brightness_quarter = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=250.0)
    expected_quarter = 100 - (250 / 1000) * 99  # ~75.25
    assert abs(brightness_quarter - expected_quarter) < 1.0


def test_lux_color_temp_at_min(tzinfo_and_location):
    """Test color temperature at minimum lux (should be warm)."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor="sensor.lux",
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    # At or below lux_min, should be warmest (min_color_temp)
    color_temp_0 = settings._color_temp_from_lux(0.0)
    assert color_temp_0 == 2000
    
    color_temp_below = settings._color_temp_from_lux(-10.0)
    assert color_temp_below == 2000


def test_lux_color_temp_at_max(tzinfo_and_location):
    """Test color temperature at maximum lux (should be cool)."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor="sensor.lux",
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    # At or above lux_max, should be coolest (max_color_temp)
    color_temp_1000 = settings._color_temp_from_lux(1000.0)
    assert color_temp_1000 == 5500
    
    color_temp_above = settings._color_temp_from_lux(2000.0)
    assert color_temp_above == 5500


def test_lux_color_temp_interpolation(tzinfo_and_location):
    """Test color temperature interpolation with lux."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor="sensor.lux",
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    # At midpoint (500 lux), should be midpoint color temp
    color_temp_mid = settings._color_temp_from_lux(500.0)
    expected_mid = (2000 + 5500) / 2  # 3750, rounded to nearest 5
    assert abs(color_temp_mid - expected_mid) <= 5


def test_lux_fallback_to_sun(tzinfo_and_location):
    """Test that sun-based calculation is used when no lux reading provided."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor="sensor.lux",
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    # At noon without lux_reading, should use sun calculation (max brightness)
    noon_time = settings.sun.noon(dt.date(2022, 6, 21))
    brightness_sun = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=None)
    assert brightness_sun == 100

    # At midnight without lux_reading, should use sun calculation (min brightness)
    midnight_time = settings.sun.midnight(dt.date(2022, 6, 21))
    brightness_midnight = settings.brightness_pct(midnight_time, is_sleep=False, lux_reading=None)
    assert brightness_midnight == 1


def test_lux_with_sleep_mode(tzinfo_and_location):
    """Test that sleep mode overrides lux-based adaptation."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=5,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor="sensor.lux",
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    noon_time = settings.sun.noon(dt.date(2022, 6, 21))
    
    # With sleep mode, should use sleep_brightness regardless of lux
    brightness_sleep = settings.brightness_pct(noon_time, is_sleep=True, lux_reading=500.0)
    assert brightness_sleep == 5


def test_lux_with_inversion(tzinfo_and_location):
    """Test that brightness inversion works with lux-based adaptation."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        invert_brightness=True,
        lux_sensor="sensor.lux",
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    noon_time = settings.sun.noon(dt.date(2022, 6, 21))
    
    # At lux_min (0), normal would be max (100), inverted should be min (1)
    brightness_inverted_min = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=0.0)
    assert brightness_inverted_min == 1
    
    # At lux_max (1000), normal would be min (1), inverted should be max (100)
    brightness_inverted_max = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=1000.0)
    assert brightness_inverted_max == 100


def test_lux_custom_range(tzinfo_and_location):
    """Test lux with custom min/max brightness range."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=80,
        max_color_temp=5500,
        min_brightness=20,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor="sensor.lux",
        lux_min=100,
        lux_max=500,
        timezone=tzinfo,
    )

    noon_time = settings.sun.noon(dt.date(2022, 6, 21))
    
    # At lux_min (100), should be max_brightness (80)
    brightness_min = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=100.0)
    assert brightness_min == 80
    
    # At lux_max (500), should be min_brightness (20)
    brightness_max = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=500.0)
    assert brightness_max == 20
    
    # At midpoint (300), should be ~50
    brightness_mid = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=300.0)
    expected = 80 - ((300 - 100) / (500 - 100)) * (80 - 20)  # 50
    assert abs(brightness_mid - expected) < 1.0


def test_lux_no_sensor_configured(tzinfo_and_location):
    """Test that lux reading is ignored when no sensor is configured."""
    from homeassistant.components.adaptive_lighting.color_and_brightness import (
        SunLightSettings,
    )

    tzinfo, location = tzinfo_and_location
    settings = SunLightSettings(
        name="test",
        astral_location=location,
        adapt_until_sleep=False,
        max_brightness=100,
        max_color_temp=5500,
        min_brightness=1,
        min_color_temp=2000,
        sleep_brightness=1,
        sleep_rgb_or_color_temp="color_temp",
        sleep_color_temp=1000,
        sleep_rgb_color=(255, 56, 0),
        sunrise_time=None,
        min_sunrise_time=None,
        max_sunrise_time=None,
        sunset_time=None,
        min_sunset_time=None,
        max_sunset_time=None,
        brightness_mode_time_dark=dt.timedelta(seconds=900),
        brightness_mode_time_light=dt.timedelta(seconds=3600),
        brightness_mode="default",
        lux_sensor=None,  # No sensor configured
        lux_min=0,
        lux_max=1000,
        timezone=tzinfo,
    )

    noon_time = settings.sun.noon(dt.date(2022, 6, 21))
    
    # Even with lux_reading provided, should use sun position since no sensor configured
    brightness = settings.brightness_pct(noon_time, is_sleep=False, lux_reading=500.0)
    assert brightness == 100  # Noon should be max brightness with sun
