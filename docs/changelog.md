<!--
SPDX-FileCopyrightText: Contributors to the Fedora Project

SPDX-License-Identifier: MIT
-->

# Changelog

All notable changes to this project will be documented in this file.

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/fedora-infra/maubot-fedora/tree/main/changelog.d/>.

<!-- towncrier release notes start -->

## [0.4.0](https://github.com/fedora-infra/maubot-fedora/tree/0.4.0) - 2023-12-07


### Added

- Send a Fedora Messaging message when a cookie is given [#20](https://github.com/fedora-infra/maubot-fedora/issues/20)


### Changed

- Changed the `!oncall` command (and associated subcommands) to `!infra oncall`. Additionally, added
  the new `!infra oncall list` command that returns the list of sysadmins that are on call, and this
  command is now aliased to `!oncall` [#26](https://github.com/fedora-infra/maubot-fedora/issues/26)
- added additional information to pagure ticket commands, including
  assignee, ticket close status, and dates of opening, modification,
  and closure. [#39](https://github.com/fedora-infra/maubot-fedora/issues/39)
- the component of a bugzilla bug is now included in the reply when using the !bug command.
  For example, previously where the reply was `RHBZ#2245223: Please update to 4.6.0` the !bug command
  will return `RHBZ#2245223: [python-pebble]: Please update to 4.6.0` [#42](https://github.com/fedora-infra/maubot-fedora/issues/42)


### Fixed

- Don't allow users to give cookies to themselves [#16](https://github.com/fedora-infra/maubot-fedora/issues/16)
- When gifting a cookie, the bot responds with "1 cookie" or "2 cookies"
  instead of "1 cookie(s)" or "2 cookie(s)". [#36](https://github.com/fedora-infra/maubot-fedora/issues/36)

## [0.3.0](https://github.com/fedora-infra/maubot-fedora/tree/0.3.0) - 2023-10-24


### Added

- The new !infra status command provides information from http://status.fedoraproject.org about
  known and upcoming outages on Fedora infrastructure. [#25](https://github.com/fedora-infra/maubot-fedora/issues/25)


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
