from __future__ import annotations


class RankingError(Exception):
    def __init__(self, error_code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.status_code = status_code


class InvalidStrategyError(RankingError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_strategy", message, 400)


class MissingRequiredParamError(RankingError):
    def __init__(self, message: str) -> None:
        super().__init__("missing_required_param", message, 400)


class InvalidAlgorithmError(RankingError):
    def __init__(self, message: str) -> None:
        super().__init__("invalid_algorithm", message, 400)


class AttributeNotFoundError(RankingError):
    def __init__(self, message: str) -> None:
        super().__init__("attribute_not_found", message, 400)


class InactiveAttributeUnavailableError(RankingError):
    def __init__(self, message: str) -> None:
        super().__init__("inactive_attribute_unavailable", message, 400)


class InternalError(RankingError):
    def __init__(self, message: str = "Unexpected server error") -> None:
        super().__init__("internal_error", message, 500)
