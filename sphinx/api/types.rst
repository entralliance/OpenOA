.. types:

Plant Data
##########

This is the core data class used to contain all data relevant to a wind plant and is used throughout
OpenOA. The :py:class:`openoa.plant.PlantData` holds multiple Pandas Data Frames, each with a
specified schema. You can take advantage of the data structures in the :py:mod:`plant` module by
creating it using one of the available constructors.

Additionally, :py:class:`openoa.plant.PlantData` requires a metadata specification, as provided
through the :py:class:`openoa.plant.PlantMetaData` class, which enable a series of data validations
that run at initialization. Optionally, this can be re-run later using
:py:class:`openoa.plant.PlantData.validate()`. Specifically, using the new
:py:class:`openoa.plant.PlantMetaData` structure, a user can map the column names already present
in their data to those that OpenOA will use internally, set the expected frequency of the their
time-dependent data, and check the expected units and datatypes that the data should use. These
configurations can be set in either a dictionary, or a metadata file using a JSON or YAML data
format, whichever is preferable to the user. In the examples, the file "examples/data/plant_meta.yml"
or "examples/data/plant_meta.json" are used interchangeably, and can be used as a guide.

Using the metadata configurations specified in a metadata file (or dictionary), an :py:class:`openoa.plant.PlantData`
object can be created as follows, where "X_df" represents a pandas DataFrame containing data
for a specific data type. Alternatively, these DataFrame arguments can be replaced by file paths to
csv files where the data are saved.::

    plant = PlantData(
        analysis_type=None,  # List of analysis methods for which the data will be validated
        metadata="{path_to_metadata_file}/plant_meta.yml",
        scada=scada_df,
        meter=meter_df,
        curtail=curtail_df,
        asset=asset_df,
        reanalysis=reanalysis_dict,
    )

The following sections will show how each of the data should be configured, and where to check for
these settings in the code itself. It should be noted that neither the :py:attr:`XMetaData.dtypes` (where "X" represents a specific data type), nor the
:py:attr:`XMetaData.units`, can be set manually, or updated as they are exclusively for reference to users.

Each of the :py:class:`XMetaData` classes accept the inputs of the elements under the column "Field Name" in
the following subsections, in addition to the frequency (:py:attr:`freq`) for time-dependent inputs. All
other attributes of the metadata classes for user reference, and therefore immutable. After setting
each of the inputs, users can access the dictionary elements :py:attr:`col_map`, :py:attr:`dtypes`, and :py:attr:`units` to
work with the various mappings. Below, is a demonstration of this mapping in practice, showing the
SCADA data mapping used in "examples/data/plant_meta.yml", where the keys are the OpenOA column names,
and the values are the La Haute Borne data naming conventions. This mapping can be repeated for each
of the other metadata types.

.. literalinclude:: ../../examples/data/plant_meta.yml
    :language: yaml
    :lines: 35-43
    :linenos:
    :lineno-start: 35



Data Schema User Guide
**********************

The following subsections will demonstrate the required data mapping schemas to enable
:py:class:`openoa.plant.PlantData` to validate and and convert user-specified data to a validated
OpenOA schema for use throughout the codebase. The data columns and their associated units and
datatypes will be shown in a table, followed by a demonstration of how this is used in the La Haute
Borne example data used for all of the example analysis workflows. It should be noted that the
column "Field Name" is the internal naming convention, and should be the dictionary or JSON/YAML
key with the actual column naming as its associated value (as is seen in the YAML snippets for each
section).

It should be noted though, that validating a :py:class:`PlantData` object with
:py:attr:`analysis_type` = "all" will check for all of the Field Names listed below for all provided
data. However, if the :py:class:`PlantData` object is only being validated for a
specific analysis type, or types, then only the data specified in
:py:const:`openoa.plant.ANALYSIS_REQUIREMENTS` (shown below) will be checked, and in the case of
:py:attr:`analysis_type` = None, then no errors will be raised during validation.

.. literalinclude:: ../../openoa/plant.py
    :language: python
    :lines: 33-72
    :linenos:
    :lineno-start: 33

SCADA
=====

:py:attr:`PlantData.scada` is configured by the :py:class:`openoa.plant.SCADAMetaData` class, which is set in the configuration
data with the "scada" key. Users can set each of the following "Field Name" keys with their own
data's column names in their SCADA data, plus the "freq" field. Users just have to ensure that the
columns are already using the specified units, and that each column is already using the listed
data type or can be converted to that type.

==================== ==================================   =============================
 Field Name           Data Type (SCADAMetaData.dtypes)     Units (SCADAMetaData.units)
==================== ==================================   =============================
 time                 datetime64[ns]                       datetime64[ns]
 id                   string                               None
 power                float                                kW
 windspeed            float                                m/s
 winddirection        float                                degrees
 status               string                               None
 pitch                float                                degrees
 temp                 float                                Celsius
==================== ==================================   =============================

.. literalinclude:: ../../examples/data/plant_meta.yml
    :language: yaml
    :lines: 35-43
    :linenos:
    :lineno-start: 35

Meter
=====

:py:attr:`PlantData.meter` is configured by the :py:class:`openoa.plant.MeterMetaData` class, which is set in the configuration
data with the "meter" key. Users can set each of the following "Field Name" keys with their own
data's column names in their SCADA data, plus the "freq" field. Users just have to ensure that the
columns are already using the specified units, and that each column is already using the listed
data type or can be converted to that type.

==================== ==================================   =============================
 Field Name           Data Type (MeterMetaData.dtypes)     Units (MeterMetaData.units)
==================== ==================================   =============================
 time                 datetime64[ns]                       datetime64[ns]
 power                float                                kW
 energy               float                                kWh
==================== ==================================   =============================

.. literalinclude:: ../../examples/data/plant_meta.yml
    :language: yaml
    :lines: 17-19
    :linenos:
    :lineno-start: 17

Tower
=====

:py:attr:`PlantData.tower` is configured by the :py:class:`openoa.plant.TowerMetaData` class, which is set in the configuration
data with the "tower" key. Users can set each of the following "Field Name" keys with their own
data's column names in their met tower data, plus the "freq" field. Users just have to ensure that
the columns are already using the specified units, and that each column is already using the listed
data type or can be converted to that type.

==================== ==================================   =============================
 Field Name           Data Type (TowerMetaData.dtypes)     Units (TowerMetaData.units)
==================== ==================================   =============================
 time                 datetime64[ns]                       datetime64[ns]
 id                   string                               None
==================== ==================================   =============================

Curtail
=======

:py:attr:`PlantData.curtail` is configured by the :py:class:`openoa.plant.CurtailMetaData` class, which is set in the configuration
data with the "curtail" key. Users can set each of the following "Field Name" keys with their own
data's column names in their curtailment data, plus the "freq" field. Users just have to ensure that
the columns are already using the specified units, and that each column is already using the listed
data type or can be converted to that type.

==================== ====================================   ===============================
 Field Name           Data Type (CurtailMetaData.dtypes)     Units (CurtailMetaData.units)
==================== ====================================   ===============================
 time                 datetime64[ns]                         datetime64[ns]
 curtailment          float                                  kWh
 availability         float                                  kWh
==================== ====================================   ===============================

.. literalinclude:: ../../examples/data/plant_meta.yml
    :language: yaml
    :lines: 9-13
    :linenos:
    :lineno-start: 9

Status
======

:py:attr:`PlantData.status` is configured by the :py:class:`openoa.plant.StatusMetaData` class, which is set in the configuration
data with the "status" key. Users can set each of the following "Field Name" keys with their own
data's column names in their turbine status data, plus the "freq" field. Users just have to ensure
that the columns are already using the specified units, and that each column is already using the
listed data type or can be converted to that type.

.. note::
    This section does not get used by OpenOA internally, though it is expected to be used in the future.


==================== ===================================   ==============================
 Field Name           Data Type (StatusMetaData.dtypes)     Units (StatusMetaData.units)
==================== ===================================   ==============================
 time                 datetime64[ns]                        datetime64[ns]
 id                   string                                None
 status_id            int                                   None
 status_code          int                                   None
 status_text          string                                None
==================== ===================================   ==============================

Asset
=====

:py:attr:`PlantData.asset` is configured by the :py:class:`openoa.plant.AssetMetaData` class, which is set in the configuration
data with the "asset" key. Users can set each of the following "Field Name" keys with their own
data's column names in their turbine and met tower asset data. Users just have to ensure that the
columns are already using the specified units, and that each column is already using the listed data
type or can be converted to that type.

==================== ==================================   =============================
 Field Name           Data Type (AssetMetaData.dtypes)     Units (AssetMetaData.units)
==================== ==================================   =============================
 id                   string                               None
 latitude             float                                WGS-84
 longitude            float                                WGS-84
 rated_power          float                                kW
 hub_height           float                                m
 rotor_diameter       float                                m
 elevation            float                                m
 type                 string                               None
==================== ==================================   =============================

.. literalinclude:: ../../examples/data/plant_meta.yml
    :language: yaml
    :lines: 1-9
    :linenos:
    :lineno-start: 1


Reanalysis
==========

:py:attr:`PlantData.reanalysis` is configured by the :py:class:`openoa.plant.ReanlysisMetaData` class, which is set in the configuration
data with the "reanalysis" key, but it should be noted that reanalysis data should be a dictionary
of settintgs for each of the reanalysis products provided. For instance, if MERRA2 and ERA5 data are
both provided, then each data set's configurations should be provided under reanalysis as dictionary
key-value pairs, where the key is the name of the reanalysis product, and the values are the
reanalysis settings for that product's data. For each product, users can set each of the following
"Field Name" keys with their own data's column names in their turbine and met tower asset data, plus
the "freq" field. Users just have to ensure that the columns are already using the specified units,
and that each column is already using the listed data type or can be converted to that type.

MERRA-2
-------

Data are based on the single-level diagnostic data available here: https://disc.gsfc.nasa.gov/datasets/M2T1NXSLV_V5.12.4/summary?keywords=%22MERRA-2%22

Wind speed and direction are taken directly from the diagnostic 50-m u- and v-wind
fields provided in this dataset. Air density at 50m is calculated using temperature
and pressure estimations at 50m and the ideal gas law. Temperature at 50m is estimated by taking the 10-m
temperature data provided by this dataset and assuming a constant lapse rate of -9.8
degrees Celsius per vertical kilometer. Pressure at 50m is extrapolated from surface pressure
data provided in this dataset using the hypsometric equation.

NCEP-2
------

Data are based on the single-level diagnostic data available here: https://rda.ucar.edu/datasets/ds091.0/

Wind speed and direction are taken directly from the diagnostic 10-m u- and v-wind
fields provided in this dataset. Air density at 10m is calculated using temperature
and pressure estimations at 10m and the ideal gas law. Temperature at 10m is estimated by taking the 2-m
temperature data provided by this dataset and assuming a constant lapse rate of -9.8
degrees Celsius per vertical kilometer. Pressure at 10m is extrapolated from surface pressure
data provided in this dataset using the hypsometric equation.

ERA5
----

Data are based on the model-level data available here: https://rda.ucar.edu/datasets/ds627.0/

Model levels are based on sigma coordinates (i.e. fractions of surface pressure). From this dataset, we
extract temperature, u-wind, and v-wind at the 58th model level, which is on average about 72m above ground level
(https://www.ecmwf.int/en/forecasts/documentation-and-support/60-model-levels). We also extract surface pressure
data. Air density at the 58th model level is calculated using temperature data extracted at that level and an estimation
of pressure at that level using the ideal gas law. Pressure at the 58th model level is extrapolated from surface pressure
data provided in this dataset using the hypsometric equation.

==================== =======================================   ==================================
 Field Name           Data Type (ReanalysisMetaData.dtypes)     Units (ReanalysisMetaData.units)
==================== =======================================   ==================================
 time                 datetime64[ns]                            datetime64[ns]
 windspeed            float                                     m/s
 windspeed_u          float                                     m/s
 windspeed_v          float                                     m/s
 wind_direction       float                                     degrees
 temperature          float                                     Kelvin
 density              float                                     kg/m^3
 surface_pressure     float                                     Pa
==================== =======================================   ==================================

.. literalinclude:: ../../examples/data/plant_meta.yml
    :language: yaml
    :lines: 20-34
    :linenos:
    :lineno-start: 20

PlantData API
*************

.. autoclass:: openoa.plant.PlantData
    :members:
    :no-undoc-members:
    :show-inheritance:


PlantMetaData API
*****************

.. autoclass:: openoa.plant.PlantMetaData
    :members:
    :no-undoc-members:
    :show-inheritance:

.. autoclass:: openoa.plant.SCADAMetaData
    :members:
    :no-undoc-members:
    :show-inheritance:

.. autoclass:: openoa.plant.MeterMetaData
    :members:
    :no-undoc-members:
    :show-inheritance:

.. autoclass:: openoa.plant.TowerMetaData
    :members:
    :no-undoc-members:
    :show-inheritance:

.. autoclass:: openoa.plant.CurtailMetaData
    :members:
    :no-undoc-members:
    :show-inheritance:

.. autoclass:: openoa.plant.StatusMetaData
    :members:
    :no-undoc-members:
    :show-inheritance:

.. autoclass:: openoa.plant.AssetMetaData
    :members:
    :no-undoc-members:
    :show-inheritance:

.. autoclass:: openoa.plant.ReanalysisMetaData
    :members:
    :no-undoc-members:
    :show-inheritance:
