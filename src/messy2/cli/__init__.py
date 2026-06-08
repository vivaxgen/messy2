# entry point


def main() -> None:
    """
    CLI entry point for messy2_mgr standalone command
    """

    # import litestar_pulse commands here tp avoid circular imports
    import litestar_pulse.cli.commands  # noqa: F401

    from .commands import messy2_mgr

    messy2_mgr()


# EOF
