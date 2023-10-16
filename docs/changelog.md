<!--
SPDX-FileCopyrightText: Contributors to the Fedora Project

SPDX-License-Identifier: MIT
-->

# Changelog

All notable changes to this project will be documented in this file.

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/fedora-infra/maubot-fedora/tree/main/changelog.d/>.

<!-- towncrier release notes start -->

## [0.2.1](https://github.com/fedora-infra/maubot-fedora/tree/0.2.1) - 2023-10-16


### Added

- Better error catching in the FASJSON client [#afa9a99](https://github.com/fedora-infra/maubot-fedora/issues/afa9a99)


### Fixed

- Fix the username matching code [#2a0d143](https://github.com/fedora-infra/maubot-fedora/issues/2a0d143)


## [0.2.0](https://github.com/fedora-infra/maubot-fedora/tree/0.2.0) - 2023-10-16


### Added

- Cookies can now be given by reacting with the cookie emoji (🍪) on messages sent by a user. [#12](https://github.com/fedora-infra/maubot-fedora/issues/12)
- Added the `!cookies` command, with two sub-commands: `!cookie give` to give a cookie to a user, and
  `!cookie count` to provide a count of a user's cookies. [#15](https://github.com/fedora-infra/maubot-fedora/issues/15)


### Changed

- Fedora Accounts user commands (`user`, `localtime`, and `hello`) are now grouped under the
  `!user` top-level command. Additionally, aliases are provided for to the previous top-level
  commands. [#13](https://github.com/fedora-infra/maubot-fedora/issues/13)
- Pagure project-specific aliases (e.g. `!fesco` or `!epel`) for the !pagureissue command are now
  defined in the maubot-fedora plugin config. [#14](https://github.com/fedora-infra/maubot-fedora/issues/14)


## [0.1.0](https://github.com/fedora-infra/maubot-fedora/tree/0.1.0) - 2023-09-30

### Changed

- Initial Release of maubot-fedora
