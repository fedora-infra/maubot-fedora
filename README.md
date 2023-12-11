# maubot-fedora
A maubot plugin for Fedora Project actions. This plugin is basically
what powers the "zodbot" bot on fedora.im.

**please note**
* meetbot is a seperate plugin, maubot-meetings
* we use [matrix-bots](https://github.com/fedora-infra/matrix-bots)
  to track overall issues for all the Fedora bots
  (so far just zodbot and meetbot)

## Current Functionality

maubot-fedora currently does the following actions:

* `!help`
* `!version`
* `!pagureissue <project> <issue_id>` - return a pagure issue
* `!whoowns <package>` - Retrieve the owner of a given package
* `!group members <groupname>` - return the members of a group
* `!group sponsors <groupname>` - return the sponsors of a group
* `!group info <groupname>` - return information about a group
* `!user hello <username>` - return brief info about a Fedora user
* `!user info <username>` - return detailed info about a Fedora user
* `!user localtime <username>` - return the current time of the user.
* `!infra oncall` & `!infra oncall list` - show who in the infra team is currently oncall
* `!infra oncall add` - Add a user to the current oncall list
* `!infra oncall remove` - Remove a user from the current oncall list
* `!infra status` - get a list of the ongoing and planned outages
* `!bug <bug_id>` - return a bugzilla bug
* `!cookie give <username>`- Give a cookie to another Fedora contributor
* `!cookie count <username>`-  Return the cookie count for a user



# Developer Documentation
## Development environment
If you are looking to try out and hack on maubot-fedora, we have a
complete development environment in the Fedora
[matrix-bots](https://github.com/fedora-infra/matrix-bots) repo.

## Release Process

1. First Bump the version in `maubot.yaml` to the version for
   the new release.

2. Process the release notes for the release with the command
   `tox -e changelog -- --version 0.4.0`
   This will update `docs/changelog.md` and remove the release notes
   files in `changelog.d/`

3. Commit these changes back to main, and push to the repo on github

4. Tag the new release: `git tag -a v0.4.0 -m"Version 0.4.0"`

5. Push the new tag to github: `git push <remote> v0.4.0`

6. Github actions will create a draft release for you on github.
   if you are happy with the release notes there, move the release
   out of draft

## Deployment

* To Deploy to staging, merge changes to the `staging` branch.
* To Deploy to production, merge changes to the `stable` branch.

once the changes are merged, the new changes will be built and
deployed to openshift.
