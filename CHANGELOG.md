# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.1.0 (2026-03-15)


### Features

* add Chinese medical terminology support to validator ([0d29021](https://github.com/Zehui127/ClinicalBench/commit/0d290211288752ae61b2a8ea3299e938ca152627))
* add clinical benchmark dataset with 6,845 tasks across 5 departments ([c764d59](https://github.com/Zehui127/ClinicalBench/commit/c764d595e5bdd360c76831abfdd76763d0cc5c68))
* add clinical benchmark tools and update gitignore ([b487762](https://github.com/Zehui127/ClinicalBench/commit/b487762ade446d311bb9aac0f02ec64313b1c58a))
* add clinical domain with 5 medical specialties ([eba5a89](https://github.com/Zehui127/ClinicalBench/commit/eba5a89c899bb9e6d3729cc1a5feafb6abbff1b4))
* add ClinicalDataEnricher module for improving clinical task quality ([5004ae7](https://github.com/Zehui127/ClinicalBench/commit/5004ae7c1271e3be2b400994ade2590eac4d0b8d))
* Add comprehensive changelog and automated release management system ([#58](https://github.com/Zehui127/ClinicalBench/issues/58)) ([f8de30c](https://github.com/Zehui127/ClinicalBench/commit/f8de30c298689cbe0117d76a378e7315a17e5bd8))
* add consultation dialogue generator and clinical domain tasks ([f38e2fc](https://github.com/Zehui127/ClinicalBench/commit/f38e2fcb3fd6d51c7c5664ed1e42bcc4ca719402))
* add medical dialogue dataset validator ([c40faec](https://github.com/Zehui127/ClinicalBench/commit/c40faecfe75c252e66d0268e5cbc930e408d979f))
* add medical dialogue datasets directory structure ([904e299](https://github.com/Zehui127/ClinicalBench/commit/904e299665476a982964f6422b080892e5e0c818))
* add medical dialogue detection module for DataQualityFiltering ([d3a7343](https://github.com/Zehui127/ClinicalBench/commit/d3a73431dcd1494e0397981bce7b67deddab665d))
* Add public leaderboard and community submission system ([bb6a9e4](https://github.com/Zehui127/ClinicalBench/commit/bb6a9e4cbda1b62fa88daa6f7ed5594c85cb0779))
* add ThReadMed-QA conversion script and documentation ([b16758e](https://github.com/Zehui127/ClinicalBench/commit/b16758ee6500248de0245cce6896dc34f76378d9))
* convert Chinese MedDialog dataset to tau2-bench format ([fda2eec](https://github.com/Zehui127/ClinicalBench/commit/fda2eec3b6938dcd1cdd9c813a531195da4a6c80))
* convert ThReadMed-QA dataset to tau2-bench format ([6c97270](https://github.com/Zehui127/ClinicalBench/commit/6c97270f03c7389b61abb33a8aacc84c7cdf0df1))
* create modular DataValidator package for medical dialogue validation ([e3d48a4](https://github.com/Zehui127/ClinicalBench/commit/e3d48a4add3a7540090c00ebb93a8e12c430cb38))
* **experiment:** Add hyperparam sweep experimental code ([#77](https://github.com/Zehui127/ClinicalBench/issues/77)) ([558e6cd](https://github.com/Zehui127/ClinicalBench/commit/558e6cd066d7bf05db587fa2dc1509765c7d03bc))
* **gym:** add Gymnasium-compatible interface for RL training ([0ed2fd8](https://github.com/Zehui127/ClinicalBench/commit/0ed2fd8d830a20657d89ae9c2efcc94838aa7129))
* massively expand medical keywords to 987 terms ([33b76dc](https://github.com/Zehui127/ClinicalBench/commit/33b76dc6741463a0e83f9a9ba7e74a605c08fc85))
* 重构为统一的医学评估框架 v2.0.0 ([abecdaf](https://github.com/Zehui127/ClinicalBench/commit/abecdafa53253174aca5386f8848a1fc3e9c8923))


### Bug Fixes

* add initial .release-please-manifest.json ([cee4902](https://github.com/Zehui127/ClinicalBench/commit/cee49027197ac4835938b4344894e1cb6050d3bc))
* add missing gymnasium dependency ([#91](https://github.com/Zehui127/ClinicalBench/issues/91)) ([a969a0c](https://github.com/Zehui127/ClinicalBench/commit/a969a0c0a29bc47ba8580107932f5298ee636045))
* communicate_info fixed to nl_assertions in Mock domain tasks ([#66](https://github.com/Zehui127/ClinicalBench/issues/66)) ([702ee77](https://github.com/Zehui127/ClinicalBench/commit/702ee77e497d89e9d8942ab7206c1a465b12e503))
* configure release-please-action with proper manifest ([dfda880](https://github.com/Zehui127/ClinicalBench/commit/dfda88048b419fc90bcf0e66e2346e312f42085b))
* correct data paths for all clinical domains ([53d4b54](https://github.com/Zehui127/ClinicalBench/commit/53d4b54578ca2c4dc21535c6163d8ce40bd5add8))
* correct type annotation in gastroenterology tools ([44535cd](https://github.com/Zehui127/ClinicalBench/commit/44535cd1d40f71537c4344f901dcfb4c5ae018dd))
* remove duplicate function definition in clinical_gastroenterology/tools.py ([3c82998](https://github.com/Zehui127/ClinicalBench/commit/3c82998b8f7b2b575c87cd6140ffa7cfb5304b6e))
* remove invalid extra-files configuration from release-please-config ([6b9562a](https://github.com/Zehui127/ClinicalBench/commit/6b9562ab8afc9121a75207073f67615499107176))
* remove invalid parameters from release-please-action ([df2920d](https://github.com/Zehui127/ClinicalBench/commit/df2920de3bb807b264807933922ced6f918d1c18))
* Remove missing submissions from manifest and add images to public directory ([#55](https://github.com/Zehui127/ClinicalBench/issues/55)) ([462578b](https://github.com/Zehui127/ClinicalBench/commit/462578b06dcc143c6ad67f75ebe08662dcb98caf))
* simplify release-please to basic configuration ([9455b48](https://github.com/Zehui127/ClinicalBench/commit/9455b484d52790080e2d09df6c11c07a047eae1b))
* update leaderboard submission validation and clarify submission types ([#155](https://github.com/Zehui127/ClinicalBench/issues/155)) ([917227c](https://github.com/Zehui127/ClinicalBench/commit/917227cedf029f1a659e339a860c738a530fd20e))
* update release-please-action to use non-deprecated version ([8466919](https://github.com/Zehui127/ClinicalBench/commit/84669194e3511dbe9d459c4f564b66da5bd76a86))


### Documentation

* add Chinese MedDialog conversion summary ([29a343c](https://github.com/Zehui127/ClinicalBench/commit/29a343c543831c20ef25960f1343c0008237ae09))
* add clinical domains integration summary ([0b9d631](https://github.com/Zehui127/ClinicalBench/commit/0b9d631637fe1f9a79617ce61f71d1cf8143e59e))
* add clinical domains overview to README ([69a8d8a](https://github.com/Zehui127/ClinicalBench/commit/69a8d8a47cfe21c5209de17169fc85e29091407d))
* add ThReadMed-QA download script and manual guide ([ee24d94](https://github.com/Zehui127/ClinicalBench/commit/ee24d94c67da3643bbdb9501296d2611b61e6049))
* unify clinical dataset directory structure and documentation ([3fd9efe](https://github.com/Zehui127/ClinicalBench/commit/3fd9efe7d0c59d59ab7fdae84325396fc08a7315))
* update README with clinical benchmark guide and fix output path ([31e235f](https://github.com/Zehui127/ClinicalBench/commit/31e235fc92b51c869b1c25a892c44137988210c4))

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.2.1] - 2025-11-07
### Added
- Gymnasium-compatible interface for RL training with `AgentGymEnv` and `UserGymEnv`
- Train/test task splits for all domains
- Interactive play mode (`tau2 play`) supporting both agent and user roles
- Possibility to strictly enforce communication protocol rules (e.g., no mixed messages with text and tool calls)

## [0.2.0] - 2025-10-06

### Added
- Web-based leaderboard system with interactive submission management
- GitHub Pages deployment for leaderboard with automated CI/CD
- Comprehensive submission validation and verification system
- Model comparison interface with performance metrics visualization
- Trajectory visualization in web interface
- Mobile-responsive leaderboard design
- Logo assets and branding for multiple LLM providers
- Live leaderboard deployment at tau-bench.com

### Changed
- Enhanced submission manifest structure
- Improved image handling and asset management
- Updated deployment workflow for better reliability

### Fixed
- Mobile view responsiveness issues
- Missing submissions from manifest
- Image path resolution for GitHub Pages deployment
- Base URL handling for subdirectory deployment

## [0.1.3] - 2025-08-26

### Fixed
- LLM arguments parsing and handling
- Removed default natural language assertion checks that were causing issues

## [0.1.2] - 2025-07-17

### Added
- `tau2 check-data` CLI command for verifying data directory setup
- Support for `TAU2_DATA_DIR` environment variable for non-editable installs
- Fallback to local source when data directory is not set
- `--num-tasks` CLI flag for limiting task count

### Changed
- Made `pip install -e .` the default installation method
- Improved task name display in CLI
- Enhanced data directory configuration flexibility

### Fixed
- Installation issues with data directory discovery
- Task filtering and display problems

## [0.1.1] - 2025-06-12

### Fixed
- Domain viewer CLI functionality
- `tau2 domain` command execution issues

## [0.1.0] - 2025-06-12

### Added
- Initial release of τ²-bench framework
- Support for multiple domains: mock, airline, retail, telecom
- Command-line interface with `tau2` command
- Agent evaluation system with LLM integration via LiteLLM
- User simulator for realistic conversation scenarios
- Environment system with domain-specific tools and policies
- Orchestration system for managing agent-user-environment interactions
- Comprehensive test suite
- Domain-specific documentation and API endpoints
- Experimental features: no-user mode, oracle-plan mode, workflow policies
- Support for ablation studies
- Interactive environment CLI for testing and debugging
- Caching system for LLM calls (Redis-based)
- Multi-trial evaluation with concurrent execution support

### Technical Details
- Python 3.10+ support
- FastAPI-based web services
- Pydantic data models
- Rich CLI with tabulated output
- Comprehensive logging with Loguru
- Performance metrics and visualization
- Configurable LLM backends
- Semantic versioning adoption

## Links
- [Repository](https://github.com/sierra-research/tau2-bench)
- [Leaderboard](https://tau-bench.com)
- [Paper](https://arxiv.org/abs/2506.07982)
- [Blog Post](https://sierra.ai/blog/benchmarking-agents-in-collaborative-real-world-scenarios)
