from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("fasjson_url")
        helper.copy("pagureio_url")
        helper.copy("pagureio_issue_aliases")
        helper.copy("forgejo_url")
        helper.copy("forgejo_issue_aliases")
        helper.copy("paguredistgit_url")
        helper.copy("bodhi_url")
        helper.copy("fedorastatus_url")
        helper.copy("controlroom")
