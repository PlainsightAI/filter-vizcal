# Changelog
Visual Calibration release notes

## [Unreleased]

## v2.0.2 - 2025-09-29
### Changed
- Fix in pakage info
  
## v2.0.1 - 2025-09-27
### Changed
- **Updated documentation**

## v2.0.0 - 2025-09-18
### Added
- **Lightweight Metrics Calculator**: Refactored from comprehensive analysis tool to configurable metrics calculator
- **Configurable Analysis Features**: Individual toggles for camera stability, video properties, and movement detection
- **Upstream Data Forwarding**: Configurable forwarding of data from upstream filters
- **Text Overlays Toggle**: Optional visual analysis information on video frames
- **Environment Variable Configuration**: Complete environment variable support for all parameters
- **Dynamic Output Naming**: Automatic generation of descriptive output video filenames
- **Comprehensive Test Suite**: Integration and smoke tests for all functionality (29 tests passing)
- **Enhanced Documentation**: Detailed README and overview documentation with usage examples
- **VS Code Debug Configuration**: Debug launch configuration for development
- **Shutdown Method**: Proper resource cleanup and logging on filter shutdown

### Changed
- **Configuration Structure**: Complete overhaul of configuration parameters
  - Removed: `subject_bool`, `output_json_path`, `model_path`, `bucket`
  - Added: `calculate_camera_stability`, `calculate_video_properties`, `calculate_movement`, `forward_upstream_data`, `show_text_overlays`, `log_interval`
- **Output Format**: Changed from JSON file output to real-time frame metadata and visual overlays
- **Usage Script**: Simplified `filter_usage.py` with environment variable support instead of hardcoded values
- **Configuration Display**: Added detailed configuration printing for better debugging
- **Output Directory Creation**: Automatic creation of output directories if they don't exist
- **Process Method**: Now returns dictionary format `{"main": Frame}` instead of single Frame object
- **String-to-Type Conversion**: Improved configuration validation with proper type conversion for all parameters

### Removed
- **JSON Data Logging**: Removed `log_data_to_json()` method and JSON file output functionality
- **Model Dependencies**: Removed model download and subject detection capabilities

### Fixed
- **Documentation**: Updated all documentation to reflect current configuration options and removed outdated references
- **Test Coverage**: Added comprehensive test coverage for configuration validation and new features
- **Error Handling**: Improved error handling and user feedback

## v1.1.0 - 2025-01-16
### Added
- **Environment Variable Configuration**: Complete environment variable support for all parameters
- **Dynamic Output Naming**: Automatic generation of descriptive output video filenames
- **Comprehensive Test Suite**: Integration and smoke tests for all functionality
- **Enhanced Documentation**: Detailed README and overview documentation with usage examples
- **VS Code Debug Configuration**: Debug launch configuration for development
- **Makefile Debug Rule**: Easy debug mode execution with `make debug`

### Changed
- **Usage Script**: Simplified `filter_usage.py` with environment variable support instead of hardcoded values
- **Configuration Display**: Added detailed configuration printing for better debugging
- **Output Directory Creation**: Automatic creation of output directories if they don't exist

### Fixed
- **Documentation**: Updated all documentation to reflect current configuration options
- **Test Coverage**: Added comprehensive test coverage for configuration validation
- **Error Handling**: Improved error handling and user feedback

## v1.0.7 - 2025-07-15
- Migrated from filter_runtime to openfilter

## v1.0.6 - 2024-03-27

### Added
- Internal improvements

## v1.0.3

### Added
- Initial Release: Visual Calibration filter for analyzing video stability and subject photometrics.

- **Video Stability Detection**
  - Uses optical flow to detect camera shake and classify video stability.
  - Tracks frame-by-frame motion and logs results.

- **Subject Photometric Analysis**
  - Optional deep model and tracker for subject movement within a ROI.
  - Outputs photometric features and tracking statistics.

- **Debug and ROI Configuration**
  - Supports setting custom ROI and model path.
  - Allows toggling subject analysis mode with `subject_bool`.

- **JSON Reporting**
  - Writes structured per-frame data and video metadata to `video_data.json`.

- **Visual Annotations**
  - Draws frame-level feedback directly on the video for easy debugging.