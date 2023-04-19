# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] [dd/mm/yyyy]

### Added
None.

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
None.

## v1.2.2 [18/04/2023]
### Changed
- (#270) updated link to user manual in welcome text

## v1.2.1 [27/02/2023]
### Fixed
- (#269) update link of AHN3 dataset to new location at pdok service

## v1.2.0 [27/10/2022]
### Added
- (#268) use partial safety factors supplied by user in segment editor in calculation of uc's and limit states for piping, uplift and heave

## v1.1.1 [25/10/2022]
### Fixed
- (#267) corrected calculation of hydraulic head to use phi_exit_average_hinterland
- (#267) reverted calculation of water level at exit point to use polder_level

## v1.1.0 [18/10/2022]
### Added
- (#264) added new field waterstand voor slootbodem, use value for drawing ditches and calculating ditch bottom

### Changed
- (#264) renamed original polder_peil field to waterstand binnendijks tijdens hoogwater
- (#264) renamed achter phi_avg field to referentie polderpeil tbhv bepalen dempingsfactor

### Removed
- (#264) removed river_phi_avg field, instead always use river_level

## v1.0.2 [30/09/2022]
### Added
- (#266) Added TNO model cutting and map visualizations for areas ICU and JAV

## v1.0.1 [27/09/2022]
### Changed
- (#265) updated link to user manual in welcome text

## v1.0.0 [05/08/2022]

### Added
- (#262) Added validation tests

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
- (#260) Fixed avg gamma for ditch cover layer

## v0.14.8 [28/07/2022]

### Added
- (#256) Added ditch geometry to flox and stix models
- (#259) Added ditch b and B to export excel

### Changed
- (#258) Added docstring for full saturation assumption

### Deprecated
None.

### Removed
None.

### Fixed
- (#256) Fixed bug for 2D cross section with 2 ditches
- (#259) Fixed h3 ditch

## v0.14.7 [26/07/2022]

### Added
None

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
- (#257) Hotfix ExitPoint params: "classified_soil_layout"

## v0.14.6 [25/07/2022]

### Added
None

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
- (#255) Fixed small bug grid exit point always showing up
- (#255) Fixed ditch geometry large_b
- 
## v0.14.5 [21/07/2022]

### Added
- (#247) Added lowest point in Hinterland
- (#247) Added two other options for the grid of exit points

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
None.

## v0.14.4 [20/07/2022]

### Added
- (#245) Added geohydro model 0
- (#245) Added possibility to overwrite phi_avg
- (#249) Added documentation link to welcome text
- (#253) Added back 3 tabs Uplift/Heave/Sellmeijer
- (#251) Added overwrite of deklaag of Exit point layout

### Changed
- (#249) Changed icon of CPT and dijkpalen
- (#249) Minor UI corrections
- (#250) Cover layer average weights is now weighted with layer thickness
- (#252) Improvement MapView of dike entity
- (#252) Link leakage length DynamicArray with scenario names

### Deprecated
None.

### Removed
None.

### Fixed
- (#254) Fixed cover layer thickness for second aquifer

## v0.14.3 [15/07/2022]

### Added
None.

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
- () Fixed bottom of cover layer height

## v0.14.2 [15/07/2022]

### Added
None.

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
- (#241) Fixed bug cover layer weights

## v0.14.1 [13/07/2022]

### Added
None.

### Changed
None.

### Deprecated
None.

### Removed
None.

### Fixed
- (#246) Fixed Piping Berekening view for weird ditches

## v0.14.0 [13/07/2022]

### Added
- (#242) Added agglomerated results view for Piping

### Changed
- (#242) PipingUtilities, changed all methods into properties

### Deprecated
None.

### Removed
- (#242) Removed Uplift/heave/sellmeijer individual views
- (#242) Removed batch download of piping results from the dike entity level

### Fixed
None.

## v0.13.2 [10/07/2022]

### Added
- (#240) Added options for the baseline of 2D longitudinal profile on dike level
- (#243) Added dijkpalen to dike entity map
- (#244) Added UserException when TNO does not cover the area around the segment for the leakage length calculation
- (#244) Added UserException when TNO model entity has been deleted.

### Changed
-(#244) Corrected UI typos

### Deprecated
None.

### Removed
None.

### Fixed
None.

## v0.13.1 [06/07/2022]

### Added
None.

### Changed
- (#239) Changed UI name TNO to 3D
- (#236) Changed ditch parser to comply with HDSR format

### Deprecated
None.

### Removed
None.

### Fixed
- (#236) Fixed intersection ditches
- (#236) Fixed several ditch related issues

## v0.13.0 [05/07/2022]

### Added
- (#235) Added UserExceptions when AHN data fetching failed
- (#235) Added boundary conditions to DGeoflow models

### Changed
- (#237) Changed bathymetry data to raster

### Deprecated
None.

### Removed
None.

### Fixed
- (#235) Fixed reverse cross section sides

## v0.12.1 [05/07/2022]

### Added
None.

### Changed
- () Changed ditches intersection from None to Intersects

### Deprecated
None.

### Removed
None.

### Fixed
None.

## v0.12.0 [03/07/2022]

### Added
- (#208) Added metadata tab to export excel
- (#233) Added import of shapefile with lat/long coordinates system
- (#221) Added GEOLib to the repo (temporary)
- (#221) Added download of .flox files
- (#234) Added UserException when making segment with too small dijvak.

### Changed
- (#231) Changed organization of dike params
- (#233) Changed max TNO size to 100Mb

### Deprecated
None.

### Removed
- (229) Removed update exit point properties

### Fixed
- (#91) Fixed non-intersecting ditches


## v0.11.6 [27/06/2022]

### Added
- (#228) Added UserException for ditch selection when bufferzone intersect center line in a weird way

### Changed
- (228) Basic renaming strings

### Deprecated
None.

### Removed
None.

### Fixed
- (#228) Fixed cross section view when no ditch was intersected by CS.


## v0.11.5 [27/06/2022]

### Added

None.

### Changed

None.

### Deprecated

None.

### Removed

- (#227) Removed Ditch, EntryLine and CrossSection entity types

### Fixed

None.

## v.0.11.4 [27/06/2022]

### Added

- Added  __init__.py

### Changed

None.

### Deprecated

None.

### Removed

None.

### Fixed

None.

## v0.11.2 [27/06/2022]

### Added

- Added back CrossSection entitytype (by accident)

### Changed

None.

### Deprecated

None.

### Removed

None.

### Fixed

None.

## v0.11.1 [27/06/2022]

### Added

- Added back EntryLine and Ditch (by accident)

### Changed

None.

### Deprecated

None.

### Removed

None.

### Fixed

None.

## v0.11.0 [27/06/2022]

### Added

- (#223) try/except for 2D soil longitunidal profile if there are too many CPT/bores
- (#215) Added sellmeijer validator
- (#225) Added try/error for exit point generation if no AHN data is retrieved
- (#225) Added progress messages for EP generation and Piping results views
- (#225) Added custom errors to be raised for piping calculation in ditches

### Changed

- (#223) Segment editor: don't fetch CPT entities in params if toggle is off

### Deprecated

None.

### Removed

None.

### Fixed

- (#215) Dijvak view can be plotted even with incomplete material table
- (#216) Fixed Leakage length stuff
- (#225) Fixed generation exit point in S-shaped ditches

## v0.10.1 [22/06/2022]

### Added

- (#222) Added welcome text to dashboard

### Changed

- (#222) Updated SDK to v13.2

### Deprecated

None.

### Removed

- (#222) Removed manifest

### Fixed

None.

## v0.10.0 [20/06/2022]

### Added

- (#207) Added scenarios to Segment entity
- (#140) Added orange marker for piping uc=infinity
- (#219) Added extension of cross section to the ExitPoint side

### Changed

- (#207) Changed piping geohydro parameters for scenarios
- (#207) Changed piping calculation function for scenarios
- (#209) Changed the building of the combined Piping layout
- (#219) Changed how the cross section is extended
- (#220) Renamed Boring and Dijkvak entity names
- (#220) Segment entity can be manually created

### Deprecated

None.

### Removed

- (#158) Removed CrossSection Ditch EntryLine entity types
- (#158) Removed step 5 in Segment editor
- (#140) Removed deprecated method in class PipingCalculation about cover layer thickness

### Fixed

- (#198) Various bug fixes and minor changes
- (#213) Fixed various feedback and bug from DK

## v0.9.1 [09/06/2022]

### Added

None.

### Changed

None.

### Deprecated

None.

### Removed

None.

### Fixed

- (#198) Various bug fixes and minor changes

## v0.9.0 [06/06/2022]

### Added

- (#185) Create a soil geometry for a flux file (stix for now)
- (#181) Added bathymetry data parsing
- (#181) Added bathymetry to cross section
- (#204) Allow user to flip the direction of the river on the cross-section
- (#202) Export output on dike level as zip for all children segments

### Changed

- (#205) Changed Opbarsten/Heave soil layout with dijvak.
- (#187) Translated UI to Dutch

### Deprecated

None.

### Removed

- (#206) Remove all 'old scenarios logic'

### Fixed

- (#203) Fixed REGIS layering
- (#210) Fixed ditches bug
- (#211) Fixed bathymetry bug
- (#212) Fixed corbetura deprecation

## v0.8.2 [31/05/2022]

### Added

None.

### Changed

- (#201) Changed the template of piping results

### Deprecated

None.

### Removed

None.

### Fixed

- () Fixed piping result bug (missing file)

## v0.8.1 [24/05/2022]

### Added

None.

### Changed

None.

### Deprecated

None.

### Removed

None.

### Fixed

- (#200) Fixed Cross section display bug

## v0.8.0 [23/05/2022]

### Added

- (#141) Added second aquifer leakage length
- (#175) Added size detection and error on csv cutter
- (#190) Added vertical line on 2D profile plot of segment entity
- (#184) Added possibility to extend cross section beyond entry line
- (#178) Allow to remove ditches from soilLayout
- (#186) Added export as Excel of Sellmeijer intermediate calculations

### Changed

- (#184) Changed to updated PlotlyView
- (#180) Use start and end chainage at segment level
- (#177) Changed UI name of segment steps
- (#176) Visualise already existing segment on dike mapview
- (#193) Changed TNO cutter script to return only points within polygon
- (#178) Refactor cross-section layout based on soilLayout 2D
- (#190) Changed the x location and width of the bars in 2d profile

### Deprecated

None.

### Removed

None.

### Fixed

- (#195) Fix DikeAPI call
- (#197) Fixed leakage length plot for single aquifer rep layout

## v0.7.1 [10/05/2022]

### Added

None.

### Changed

None.

### Deprecated

None.

### Removed

None.

### Fixed

- (#189) Fixed memoization bug of TNO file in production

## v0.7.0 [09/05/2022]

### Added

- (#64) Added 2D cross-section in exit-point
- (#122) Added possibility to download a cut-down csv in Models folder entity
- (#143) Added bottom of soil layout to soil layout table on dyke level
- (#151) Added download for segment trajectory on dyke level
- (#152) Added colorbars to the permeability 2D soil profile
- (#154) Added aquifer properties fields on dike level
- (#154) Added dijvak visualization on segment level
- (#145) Added numbering for leakage points and visualisation of soil layout at leakage point
- (#162) Added on segment level: tab soil schematization
- (#164) Added visualisation of chosen TNO model on models folder level
- (#150) Added segment entity creation by interval and segment interval visualization
- (#167) Added simplified rep soil layout of segment
- (#167) Added effective calculation of aquifer properties
- (#167) Added visualization of both detailed and simplified rep soil layout

### Changed

- (#160) Concentrated TNO parsing to the TNOModel object rather than methods on the segment controller
- (#153) CPT and 2d layout improvement
- (#149) Changed segment creation from user selected polygon to start and end chainage
- (#136) Refactor get_visualisation_along_trajectory
- (#171) Show only segment 2D longitudinal profile on segment level
- (#169) Changed leakage length logic with new rep soil layout
- (#170) Changed Sellmeijer calculation with new rep soil layout

### Deprecated

None.

### Removed

- (#162) Removed section on dike level: Representative soil layout

### Fixed

- (#166) Fixed Get soil layout button on segment level
- (#169) Fixed fixtures materials table
- (#173) Fixed bug with CPT without u2 on 2D profile
- (#174) Fixed fetch AHN try/except

## v0.6.0 [27/04/2022]

### Added

- (#126) Added segment blue box on 2D soil profile
- (#126) Added memoization of the TNO model import on dike level
- (#121) Added Text explanation about geoHydro model
- (#133) Added switch of TNO/classfied layout for the leakage length TopView
- (#136) Added boreholes to application
- (#110) Added representative layout of segment as a SoilLayout object
- (#131) Added possibility to change base line for 2D soil profile
- (#144) Added all parameters passed into representative layout

### Changed

- (#127) Changed Antropogeen grond UI name to Niet geclassificeerd
- (#132) Agglomerated TNO layer on dike entity
- (#125) Automatic detection of chainage length from ground model
- (#137) Modified heave and uplift calculations
- (#126) Representative soil layout is classified in the dike soil layout table
- (#126) Changed the determination of a representative layout
- (#134) Changed determination of leakage length from representative layout
- (#135) Changed ditches adn entry line to FileFields
- (#110) Refactor Soil layout inspection
- (#111) Changed Sellmeijer calculation to accomodate for representative soil layout
- (#147) Split the dyke trajectory and trajectory used for 2D soil layout visualisation
- (#191) Add regis model to visualisation of the 2D soil Layout

### Deprecated

None.

### Removed

None.

### Fixed

- (#139) Fixed manifest dike fixture
- (#142) Fixed soil inspection view
- (#148) Fixed dike MapView error
- (#146) Fixed bug if exit point layout does not have an aquifer

## v0.5.0 [11/04/2022]

### Added

- (#113) Added new step for the calculation of the leakage length
- (#113) Added MapAndDataView for visualization of the leakage length per voxel
- (#119) Tests for Dyke entity
- (#101) Added a button to automatically select the closest CPT for soil layout inspection
- (#101) Added CPT to maps on Segment level
- (#107) Added possibility to switch TNO/classified soil layout
- (#108) Display chainage (metrering) in the dyke ui
-

### Changed

- (#119) DykeAPi is now based on API helper
- (#95) Changed pygeo library to rtree
- (#120) Reorganised dike MapView and added CPT labels
- (#105) Mocked ahn API

### Deprecated

None.

### Removed

None.

### Fixed

- (#95) Fixed Deprecation warning
- (modify_ditch_calculation) Fixed ground level in piping utilities
- (#123) Fixed reset of soil layout
- (#123) Reset segment drawing option to None on dike level

## v0.4.0 [04/04/2022]

### Added

- (#86) Added definition of the ditch params
- (#86) Added ditches parameters to exit point
- (#100) Added parsing of onderhoudiepte from ditch files
- (#106) Added visualisation of TNO model along dyke trajectory

### Changed

- (#102) Modified ditches parameters and update uplift calculation
- (#103) Re-ordered the draft exit point creation for naming purposes

### Deprecated

None. git

### Removed

None.

### Fixed

- (#86) Fixed CI bug when running black
- (#77) Fixed Exit point bug with soil layout without aquifer
- (#77) Fixed intersection soil layout bug when ahn_z is nan
- (#104 Fixed ditches polygon created in wrong direction
- (#66) Fixed Sellmeijer calculations
- (#116) ReFixed Sellmeijer calculations: GAMMA_P_SUB is fixed for F_1
- (#114) Fixed a bug with ditches and Exit point generations

## v0.3.0 [28/03/2022]

### Added

None.

### Changed

- (#67) Add leakage length to scenarios
- (#84) Changed editor of segment into stepwise
- (#92) Exclude ditches from hinterland polygon
- (#94) Implement buffer zone with offset from crest line

### Deprecated

None.

### Removed

None.

### Fixed

None.

## v0.2.3 [14/03/2022]

### Added

None.

### Changed

None.

### Deprecated

None.

### Removed

None.

### Fixed

- (#80) Fixed generation of exit point location
- (#81) Fixed a few error catching

## v0.2.2 [14/03/2022]

### Added

None.

### Changed

- (#79) Prior filtering TNO model around location of exit point

### Deprecated

None.

### Removed

None.

### Fixed

None.

## v0.2.1 [11/03/2022]

### Added

None.

### Changed

- (fix_memory_issue_production) Refactored tno conversion to fix memory issue

### Deprecated

None.

### Removed

None.

### Fixed

None.

## v0.2.0 [11/03/2022]

### Added

- (#55) Added generation of scenarios
- (#65) Added iteration of scenarios for piping calculations
- (#XX) Added more segment integration tests
- (#71) Added Upload of ditch shapefiles to Ditch Entity
- (#71) Added Mapview for visualization of ditches

### Changed

None.

### Deprecated

None.

### Removed

None.

### Fixed

- (#74) Fixed API calls for uplifting calculations

### Security

None.

## v0.1.0 [02/03/2022]

### Added

- (#1) Initial repository structure
- (#3) Added Models folder and TNO Ground model entity types
- (#3) Added process file for TNO Ground model entity
- (#3) Added MapPolygon of TNO model on Dyke entity MapView
- (#3) Added MapView for TNO Ground Model entity
- (#5) Added upload of shapefiles for creation of dyke entity
- (#5) Added Map visualisation of main line of dyke
- (#12) Added dummy OptionFields for geohydro model and soil materials
- (#17) Added CPTFolder and CPT entity types to manifest
- (#17) Added simplified CPT controller based on Geo-tools
- (#9) Added cross section table to Segment entity
- (#9) Added Mapview to Segment entity with dyke trajectory, segment and cross sections
- (#16) Allow user to select dyke orientation
- (#18) Added button for creation of cross section entities on Segment level
- (#18) Added basic MapView to cross-section entity
- (#11) Added Views to cross section entity
- (#24) Added custom TNOSoilLayout class
- (#24) Added GroundProfile TNO class
- (#21) Added creation of the exit point entity
- (#29) Added Soil layout table for a selected point in segment entity
- (#31) Update soil layout in batches of exit points
- (#29) Added Soil layout table for a selected point in segment entity
- (#33) Added library for uplifting calculation
- (#33) Added visualization of uplifting calculation
- (#34) Added Snellmeijer piping calculation
- (#40) Separated tno and user soil layout in ExitPoint parametrization
- (#35) Added Heave limit state to PipingCalculation class
- (#42) Added soil material and classification tables
- (#25) Added helper functions to parse AHN data
- (#46) Added classification of the TNO soil layout based on material and classification tables
- (#38) Added distance between exit point and crest line/entry line
- (#25) Added helper functions to parse AHN data
- (#54) Added manually selection of exit points
- (#52) Added Mapview for heave and Sellmeiejr results
- (#44) Connect exit point location with AHN level
- (#50) Replaced first value of layer table with ahn
- (#58) Added API library helper
- (#58) Added integration tests for segment
- (#52) Added Mapview for heave and Sellmeiejr results
- (#61) Added fixtures template for unittests
- (#32) Added summary of ExitPoint entities
- (#88) Added leakage lengths to material table
- (#93) Added all tno information on hover textbox of layout inspection
- (#94) Implemented buffer zone with offset from crest line
- (#109) Added representative soil layout functionality to dike entity
- (#141) Added vertical and horizontal permeability visualisation in 2D section
- (#130) Added CPT traces to 2D profile figure

### Changed

- (#13) Changing max_size file upload of TNO GroundModel to 200MB
- (#9) Refactored conversion of segment GeoPolygon into Polyline along dyke trajectory
- (#14) refactor segement map view and fix duplicate code
- (#40) Connected the ExitPoint entity properties with Piping calculations
- (#51) Changed Soil layout inspection to include third row based on predictive user soil table
- (#49) Improved Soil Layout visualization
- (#54) Changed generation of draft exit points location
- (#54) Changed the naming of the exit point entities
- (#46) Changed default classification table
- (#52) Changed Uplift/heave/Sellmeijer calculations to accomodate multi layer cover
- (#49) Improved Soil Layout visualization
- (#56) Shuffled visualisation settings
- (#58) Overhauled the API library
- (#52) Changed Uplift/heave/Sellmeijer calculations to accomodate multi layer cover
- (#78) Generate exit points along ditches lines instead of with a polygon

### Deprecated

None.

### Removed

None.

### Fixed

- (#26) Fixed the import of the TNO ground model points
- (#40) Fixed set_params of the update Exit point button
- (#49) Fixed passing Aquifer attribute during conversion of soil layout table
- (#57) Fixed DEFAULT_CLASSIFICATION_TABLE
- (#69) Fixed annoying error messages

### Security

None.
