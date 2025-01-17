from __future__ import annotations

from copy import deepcopy

import attr
import numpy as np
import pandas as pd
import pytest
from attrs import field, define

from openoa.plant import (  # , compose_error_message
    ANALYSIS_REQUIREMENTS,
    PlantData,
    AssetMetaData,
    FromDictMixin,
    MeterMetaData,
    PlantMetaData,
    SCADAMetaData,
    TowerMetaData,
    StatusMetaData,
    CurtailMetaData,
    ReanalysisMetaData,
    load_to_pandas,
    rename_columns,
    convert_to_list,
    dtype_converter,
    _at_least_hourly,
    column_validator,
    convert_reanalysis,
    frequency_validator,
    load_to_pandas_dict,
)


# Test the FromDictMixin mixin class and class-dependent methods


@define
class AttrsDemoClass(FromDictMixin):
    w: int
    x: int = field(converter=int)
    y: float = field(converter=float, default=2.1)
    z: str = field(converter=str, default="z")


def test_FromDictMixin_defaults():
    # Test that the defaults set in the class definition are actually used
    inputs = {"w": 0, "x": 1}
    cls = AttrsDemoClass.from_dict(inputs)
    defaults = {a.name: a.default for a in AttrsDemoClass.__attrs_attrs__ if a.default}
    assert cls.y == defaults["y"]
    assert cls.z == defaults["z"]

    # Test that defaults can be overwritten
    inputs = {"w": 0, "x": 1, "y": 4.5}
    cls = AttrsDemoClass.from_dict(inputs)
    defaults = {a.name: a.default for a in AttrsDemoClass.__attrs_attrs__ if a.default}
    assert cls.y != defaults["y"]


def test_FromDictMixin_custom():
    # Test the FromDictMixin class with non-default values
    inputs = {
        "w": 0,
        "x": 1,
        "y": 2.3,
        "z": "asdf",
        "liststr": ["a", "b"],
    }

    # Check that custom inputs are accepted
    AttrsDemoClass.from_dict(inputs)

    # Test that missing required inputs raises an error
    inputs = {}
    with pytest.raises(AttributeError):
        AttrsDemoClass.from_dict(inputs)


# Test all the standalone utility/helper methods


def test_frequency_validator() -> None:
    """Tests the `frequency_validator` method. All inputs are formatted to the desired input,
    so testing of the input types is not required.
    """

    # Test None as desired frequency returns True always
    assert frequency_validator("anything", None, exact=True)
    assert frequency_validator("anything", None, exact=False)
    assert frequency_validator(None, None, exact=True)
    assert frequency_validator(None, None, exact=False)

    # Test None as actual frequency returns False as long as desired isn't also True (checked above)
    assert not frequency_validator(None, "anything", exact=True)
    assert not frequency_validator(None, "whatever", exact=False)

    # Test for exact matches
    actual = "10T"
    desired_valid_1 = "10T"  # single input case
    desired_valid_2 = ("10T", "H", "N")  # set of options case
    desired_invalid = _at_least_hourly  # set of non exact matches

    assert frequency_validator(actual, desired_valid_1, True)
    assert frequency_validator(actual, desired_valid_2, True)
    assert not frequency_validator(actual, desired_invalid, True)

    # Test for non-exact matches
    actual_1 = "10T"
    actual_2 = "1min"
    actual_3 = "20S"
    desired_valid = _at_least_hourly  # set of generic hourly or higher resolution frequencies
    desired_invalid = (
        "M",
        "MS",
        "W",
        "D",
        "H",
    )  # set of greater than or equal to hourly frequency resolutions

    assert frequency_validator(actual_1, desired_valid, False)
    assert frequency_validator(actual_2, desired_valid, False)
    assert frequency_validator(actual_3, desired_valid, False)
    assert not frequency_validator(actual_1, desired_invalid, False)
    assert not frequency_validator(actual_2, desired_invalid, False)
    assert not frequency_validator(actual_3, desired_invalid, False)


def test_convert_to_list():
    """Tests the converter function for turning single inputs into a list of input,
    or applying a manipulation across a list of inputs
    """

    # Test that a list of the value is returned
    assert convert_to_list(1) == [1]
    assert convert_to_list(None) == [None]
    assert convert_to_list("input") == ["input"]
    assert convert_to_list(42.8) == [42.8]

    # Test that the same list is returned
    assert convert_to_list(range(3)) == [0, 1, 2]
    assert convert_to_list([44, "six", 1.2]) == [44, "six", 1.2]
    assert convert_to_list((44, "six", 1.2)) == [44, "six", 1.2]

    # Test that an invalid type is passed to the manipulation argument
    with pytest.raises(TypeError):
        assert convert_to_list(range(3), str.upper)

    # Test that lists of mixed inputs error out with a type-specific converter function

    with pytest.raises(ValueError):
        assert convert_to_list(["?", "one", "string", 2], float)

    # Test that valid manipulations work
    assert convert_to_list(range(3), float) == [0.0, 1.0, 2.0]
    assert convert_to_list([1.1, 2.2, 3.9], int) == [1, 2, 3]
    assert convert_to_list(["loud", "noises"], str.upper) == ["LOUD", "NOISES"]
    assert convert_to_list(["quiet", "VOICes"], str.lower) == ["quiet", "voices"]


def test_column_validator():
    """Tests the `column_validator` method to ensure dataframes contain all of the
    required columns.
    """
    df = pd.DataFrame([range(4)], columns=[f"col{i}" for i in range(1, 5)])

    # Test for a complete match
    col_map = {f"new_col_{i}": f"col{i}" for i in range(1, 5)}
    assert column_validator(df, column_names=col_map) == []

    # Test for a partial match with extra columns causing no issue at all
    col_map = {f"new_col_{i}": f"col{i}" for i in range(1, 3)}
    assert column_validator(df, column_names=col_map) == []

    # Test for an incomplete match
    col_map = {f"new_col_{i}": f"col{i}" for i in range(1, 6)}
    assert column_validator(df, column_names=col_map) == ["col5"]


def test_dtype_converter():
    """Tests the `dtype_converter` method to ensure that columns get converted
    correctly or return a list of error columns. This assumes that datetime columns
    have already been converted to pandas datetime objects in the reading methods.
    """
    df = pd.DataFrame([], columns=["time", "float_col", "string_col", "problem_col"])
    df.time = pd.date_range(start="2022-July-25 00:00:00", end="2022-July-25 1:00:00", freq="10T")
    df.float_col = np.random.random(7).astype(str)
    df.string_col = np.arange(7)
    df.problem_col = ["one", "two", "string", "invalid", 5, 6.0, 7]

    column_types_invalid_1 = dict(
        time=pd.DatetimeIndex, float_col=float, string_col=str, problem_col=float
    )
    column_types_invalid_2 = dict(
        time=np.datetime64, float_col=float, string_col=str, problem_col=int
    )
    column_types_valid = dict(time=np.datetime64, float_col=float, string_col=str, problem_col=str)

    assert dtype_converter(df, column_types_invalid_1) == ["problem_col"]
    assert dtype_converter(df, column_types_invalid_2) == ["problem_col"]
    assert dtype_converter(df, column_types_valid) == []


def test_analysis_filter():
    # Save for later
    pass


def test_compose_error_message():
    # Potentially goes with test_analysis_filter, but passing on them both for now
    pass


def test_load_to_pandas():
    # Save for later
    pass


def test_load_to_pandas_dict():
    # Save for later
    pass


def test_rename_columns():
    """Tests the `rename_columns` method for renaming dataframes."""
    df = pd.DataFrame([range(4)], columns=[f"col{i}" for i in range(1, 5)])
    col_map = {f"col{i}": f"new_col_{i}" for i in range(1, 5)}

    # Test for a standard mapping
    new_df = rename_columns(df, col_map, reverse=False)
    assert new_df.columns.to_list() == list(col_map.values())

    # Test for the reverse case
    new_df = rename_columns(df, col_map, reverse=True)
    assert new_df.columns.to_list() == list(col_map.keys())


# Test the Metadata objects


def test_SCADAMetaData():
    # Tests the SCADAMetaData for defaults and user-provided values

    # Leaving id and power as the default values
    meta_dict = dict(
        time="datetime",
        windspeed="ws_100",
        wind_direction="wd_100",
        status="turb_stat",
        pitch="rotor_angle",
        temperature="temp",
        frequency="H",
    )
    valid_map = deepcopy(meta_dict)
    valid_map.update(dict(id="id", power="power"))
    valid_map.pop("frequency")

    meta = SCADAMetaData.from_dict(meta_dict)
    cols = deepcopy(meta.col_map)
    cols.pop("energy")  # need to move the internally-set mapping
    assert cols == valid_map
    assert meta.frequency == meta_dict["frequency"]

    # Ensure the defaults are the defaults
    assert meta.units == attr.fields(SCADAMetaData).units.default
    assert meta.dtypes == attr.fields(SCADAMetaData).dtypes.default

    # Test that non-init elements can't be set
    with pytest.raises(TypeError):
        SCADAMetaData(units={})

    with pytest.raises(TypeError):
        SCADAMetaData(dtypes={})


def test_MeterMetaData():
    # Tests the MeterMetaData for defaults and user-provided values

    # Leaving time and energy as the default values
    meta_dict = dict(
        power="power_production",
        frequency="D",
    )
    valid_map = deepcopy(meta_dict)
    valid_map.update(dict(time="time", energy="energy"))
    valid_map.pop("frequency")

    meta = MeterMetaData.from_dict(meta_dict)
    assert meta.col_map == valid_map
    assert meta.frequency == meta_dict["frequency"]

    # Ensure the defaults are the defaults
    assert meta.units == attr.fields(MeterMetaData).units.default
    assert meta.dtypes == attr.fields(MeterMetaData).dtypes.default

    # Test that non-init elements can't be set
    with pytest.raises(TypeError):
        MeterMetaData(units={})

    with pytest.raises(TypeError):
        MeterMetaData(dtypes={})


def test_TowerMetaData():
    # Tests the TowerMetaData for defaults and user-provided values

    # Leaving time as the default value
    meta_dict = dict(
        id="the_IDs",
        frequency="D",
    )
    valid_map = deepcopy(meta_dict)
    valid_map.update(dict(time="time"))
    valid_map.pop("frequency")

    meta = TowerMetaData.from_dict(meta_dict)
    assert meta.col_map == valid_map
    assert meta.frequency == meta_dict["frequency"]

    # Ensure the defaults are the defaults
    assert meta.units == attr.fields(TowerMetaData).units.default
    assert meta.dtypes == attr.fields(TowerMetaData).dtypes.default

    # Test that non-init elements can't be set
    with pytest.raises(TypeError):
        TowerMetaData(units={})

    with pytest.raises(TypeError):
        TowerMetaData(dtypes={})


def test_StatusMetaData():
    # Tests the StatusMetaData for defaults and user-provided values

    # Leaving time and status_text as the default values
    meta_dict = dict(
        id="the_IDs",
        status_id="status_ids",
        status_code="code",
        frequency="H",
    )
    valid_map = deepcopy(meta_dict)
    valid_map.update(dict(time="time", status_text="status_text"))
    valid_map.pop("frequency")

    meta = StatusMetaData.from_dict(meta_dict)
    assert meta.col_map == valid_map
    assert meta.frequency == meta_dict["frequency"]

    # Ensure the defaults are the defaults
    assert meta.units == attr.fields(StatusMetaData).units.default
    assert meta.dtypes == attr.fields(StatusMetaData).dtypes.default

    # Test that non-init elements can't be set
    with pytest.raises(TypeError):
        StatusMetaData(units={})

    with pytest.raises(TypeError):
        StatusMetaData(dtypes={})


def test_CurtailMetaData():
    # Tests the CurtailMetaData for defaults and user-provided values

    # Leaving time and net_energy as the default values
    meta_dict = dict(
        curtailment="curtail",
        availability="avail",
        frequency="H",
    )
    valid_map = deepcopy(meta_dict)
    valid_map.update(dict(time="time"))
    valid_map.pop("frequency")

    meta = CurtailMetaData.from_dict(meta_dict)
    assert meta.col_map == valid_map
    assert meta.frequency == meta_dict["frequency"]

    # Ensure the defaults are the defaults
    assert meta.units == attr.fields(CurtailMetaData).units.default
    assert meta.dtypes == attr.fields(CurtailMetaData).dtypes.default

    # Test that non-init elements can't be set
    with pytest.raises(TypeError):
        CurtailMetaData(units={})

    with pytest.raises(TypeError):
        CurtailMetaData(dtypes={})


def test_AssetMetaData():
    # Tests the AssetMetaData for defaults and user-provided values

    # Leaving elevation and type as the default values
    meta_dict = dict(
        id="asset_name",
        latitude="lat",
        longitude="lon",
        rated_power="P",
        hub_height="HH",
        rotor_diameter="RD",
    )
    valid_map = deepcopy(meta_dict)
    valid_map.update(dict(elevation="elevation", type="type"))

    meta = AssetMetaData.from_dict(meta_dict)
    assert meta.col_map == valid_map

    # Ensure the defaults are the defaults
    assert meta.units == attr.fields(AssetMetaData).units.default
    assert meta.dtypes == attr.fields(AssetMetaData).dtypes.default

    # Test that non-init elements can't be set
    with pytest.raises(TypeError):
        AssetMetaData(units={})

    with pytest.raises(TypeError):
        AssetMetaData(dtypes={})


def test_ReanalysisMetaData():
    # Tests the ReanalysisMetaData for defaults and user-provided values

    # Leaving temperature, density, and frequency as the default values
    meta_dict = dict(
        time="curtail",
        windspeed="WS",
        windspeed_u="ws_U",
        windspeed_v="ws_V",
        wind_direction="wdir",
        surface_pressure="pressure",
    )
    valid_map = deepcopy(meta_dict)
    valid_map.update(dict(temperature="temperature", density="density"))

    meta = ReanalysisMetaData.from_dict(meta_dict)
    assert meta.col_map == valid_map

    # Ensure the defaults are the defaults
    assert meta.units == attr.fields(ReanalysisMetaData).units.default
    assert meta.dtypes == attr.fields(ReanalysisMetaData).dtypes.default
    assert meta.frequency == attr.fields(ReanalysisMetaData).frequency.default

    # Test that non-init elements can't be set
    with pytest.raises(TypeError):
        ReanalysisMetaData(units={})

    with pytest.raises(TypeError):
        ReanalysisMetaData(dtypes={})


def test_convert_reanalysis_value():
    # Test the ReanalysisMetaData dictionary converter method

    # Leaving the merra2 key as all defaults
    era5_meta_dict = dict(
        time="curtail",
        windspeed="WS",
        windspeed_u="ws_U",
        windspeed_v="ws_V",
        wind_direction="wdir",
        temperature="temps",
        density="dens",
        surface_pressure="pressure",
        frequency="5T",
    )
    valid_era5_map = deepcopy(era5_meta_dict)
    valid_era5_map.pop("frequency")

    # Copy of the defaults
    valid_merra2_map = dict(
        time="time",
        windspeed="windspeed",
        windspeed_u="windspeed_u",
        windspeed_v="windspeed_v",
        wind_direction="wind_direction",
        temperature="temperature",
        density="density",
        surface_pressure="surface_pressure",
    )

    meta = convert_reanalysis(value=dict(era5=era5_meta_dict, merra2=dict()))
    assert meta["era5"].col_map == valid_era5_map
    assert meta["era5"].frequency == era5_meta_dict["frequency"]

    # Ensure the defaults are the defaults
    assert meta["era5"].units == attr.fields(ReanalysisMetaData).units.default
    assert meta["era5"].dtypes == attr.fields(ReanalysisMetaData).dtypes.default

    assert meta["merra2"].col_map == valid_merra2_map
    assert meta["merra2"].frequency == attr.fields(ReanalysisMetaData).frequency.default
    assert meta["merra2"].units == attr.fields(ReanalysisMetaData).units.default
    assert meta["merra2"].dtypes == attr.fields(ReanalysisMetaData).dtypes.default


def test_PlantMetaData_defaults():
    # Test the PlantMetaData object

    # Test the default values only for meta data because all the subcomponents have been checked
    meta = PlantMetaData()
    assert meta.latitude == 0.0
    assert meta.longitude == 0.0
    assert meta.scada == SCADAMetaData()
    assert meta.meter == MeterMetaData()
    assert meta.tower == TowerMetaData()
    assert meta.status == StatusMetaData()
    assert meta.curtail == CurtailMetaData()
    assert meta.asset == AssetMetaData()
    assert meta.reanalysis == {}

    # Test the coordinates property
    assert meta.coordinates == (0.0, 0.0)

    # Test the column_map property
    vals = meta.column_map
    assert vals["scada"] == SCADAMetaData().col_map
    assert vals["meter"] == MeterMetaData().col_map
    assert vals["tower"] == TowerMetaData().col_map
    assert vals["status"] == StatusMetaData().col_map
    assert vals["curtail"] == CurtailMetaData().col_map
    assert vals["asset"] == AssetMetaData().col_map
    assert vals["reanalysis"] == {}

    # Check the defaults for an empty reanalysis input
    meta = PlantMetaData(reanalysis=dict(era5=ReanalysisMetaData().col_map))
    assert meta.reanalysis == dict(era5=ReanalysisMetaData())
    vals = meta.column_map
    assert vals["reanalysis"]["era5"] == ReanalysisMetaData().col_map


# def test_PlantMetaData_from_yaml():
#     # Test the PlantMetaData object using the from_yaml classmethod

#     # Test the default values only for meta data because all the subcomponents have been checked
#     meta = PlantMetaData.from_yaml(need to create the test data)
#     assert meta.latitude == 0.0
#     assert meta.longitude == 0.0
#     assert meta.scada == SCADAMetaData()
#     assert meta.meter == MeterMetaData()
#     assert meta.tower == TowerMetaData()
#     assert meta.status == StatusMetaData()
#     assert meta.curtail == CurtailMetaData()
#     assert meta.asset == AssetMetaData()
#     assert meta.reanalysis == {}

#     # Test the coordinates property
#     assert meta.coordinates == (0.0, 0.0)

#     # Test the column_map property
#     vals = meta.column_map
#     assert vals["scada"] == SCADAMetaData().col_map
#     assert vals["meter"] == MeterMetaData().col_map
#     assert vals["tower"] == TowerMetaData().col_map
#     assert vals["status"] == StatusMetaData().col_map
#     assert vals["curtail"] == CurtailMetaData().col_map
#     assert vals["asset"] == AssetMetaData().col_map
#     assert vals["reanalysis"] == {}
