from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

class ArgsUtils():

    @staticmethod
    def initialiseParser(scriptUsesMealieApi: bool = False):
        parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)

        parser.add_argument(
            "-v",
            "--verbosity",
            help="Verbosity level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO"
        )

        parser.add_argument(
            "-d",
            "--dryRun",
            help="No-op; will not modify resources",
            action="store_true"
        )

        if scriptUsesMealieApi:
            parser.add_argument(
                "-u",
                "--url",
                help="URL to Mealie instance",
                required=True
            )

            parser.add_argument(
                "-t",
                "--token",
                help="Mealie API token",
                required=True
            )

            parser.add_argument(
                "-c",
                "--caPath",
                help="Path to CA bundle used to verify Mealie TLS certificate",
                default=None
            )

            parser.add_argument(
                "--cacheDuration",
                help="Number of seconds after which cached requests will expire."
                " Set to -1 to disable expiration."
                " Set to 0 to disable cacheing.",
                default=3600 # 1 hour
            )

        return parser
