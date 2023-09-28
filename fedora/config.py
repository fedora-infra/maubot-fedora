from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper


class Config(BaseProxyConfig):
    def do_update(self, helper: ConfigUpdateHelper) -> None:
        helper.copy("fasjson_url")
        helper.copy("pagureio_url")
        helper.copy("paguredistgit_url")
        helper.copy("controlroom")
