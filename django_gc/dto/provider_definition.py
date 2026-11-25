from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ProviderDefinition:
    """
    Register a provider by its dotted class path and assign an ID to each of its category codes.

    The integrating project coordinates numeric IDs across its own categories and all installed providers.
    """

    provider: str
    category_ids: dict[str, int]
