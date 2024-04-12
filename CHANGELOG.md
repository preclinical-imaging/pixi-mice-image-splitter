# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
