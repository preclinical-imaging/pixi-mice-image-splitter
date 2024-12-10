# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2024-12-09

- [PIXI-156] - Add injection date to the hotel scan record form. Sometimes animals are injected on a different day than
               the scan is performed.
- [PIXI-158] - Update hotel splitter to reuse a single session when calling XNAT instead of creating a new session for
               each request. This will reduce the number of user sessions created in XNAT.


## [0.2.4] - 2024-11-19

### Added

- [PIXI-155] - Technician perspective field added to the hotel scan record form. The front/back perspectives can be
               selected for the hotel scan record. The image will be rotated accordingly during the splitting process
               if the perspective is set to back.

## [0.2.3] - 2024-10-31

- [PIXI-152] - Enable single mouse hotels. Keeps a consistent workflow for single and multiple mouse hotels and 
               will crop the single mouse hotel to the same size as the multiple mouse hotel split images.

## [0.2.2] - 2024-09-24

### Fixed

- [PIXI-148] - Fix issue with Inveon CT sessions splitting not detecting enough regions. Will now adjust the threshold
               for region detection and try again until enough regions are detected.
- [PIXI-149] - Fix issues with Inveon hdr metadata not being written correctly for the split images.

## [0.2.1] - 2024-07-02

### Fixed

- [PIXI-146]: Fix issue with handling more than 4 detected regions. Will attempt to merge regions in the same quadrant
              if more than 4 regions are detected.

## [0.2.0] - 2024-06-24

### Added

- [PIXI-136]: Update hotel splitter wrapper to support native Inveon images.

## [0.1.2] - 2024-04-12

### Fixed

- [PIXI-126] - Fix string concatenation TypeError in the `splitter_of_mice` package.
- [PIXI-129] - Fix issue with empty subject id's in the hotel record being counted as a valid subject.
- [PIXI-129] - Fix issue with error not being raised when PET splitting failed.

### Changed

- [PIXI-129] - When re-splitting a hotel scan, the existing image sessions will now be deleted before uploading the new 
               split images.

## [0.1.1] - 2024-01-31

### Fixed

- Change the status method sent to PIXI hotel scan record to match what is expected by the PIXI plugin. The 
  image acquisition context was not being split to the newly imported and archived image sessions.

### Changed

- Merge XNAT Container Service command JSONs into a single file for easier management.

## [0.1.0] - 2024-01-30

Initial release of the PIXI Mice Image Splitter and Docker image.


[PIXI-126]: https://radiologics.atlassian.net/browse/PIXI-126
[PIXI-129]: https://radiologics.atlassian.net/browse/PIXI-129
[PIXI-136]: https://radiologics.atlassian.net/browse/PIXI-136
[PIXI-146]: https://radiologics.atlassian.net/browse/PIXI-146
[PIXI-148]: https://radiologics.atlassian.net/browse/PIXI-148
[PIXI-149]: https://radiologics.atlassian.net/browse/PIXI-149
[PIXI-155]: https://radiologics.atlassian.net/browse/PIXI-155
[PIXI-156]: https://radiologics.atlassian.net/browse/PIXI-156
[PIXI-158]: https://radiologics.atlassian.net/browse/PIXI-158