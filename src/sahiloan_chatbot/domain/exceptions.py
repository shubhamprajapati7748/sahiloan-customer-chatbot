"""Domain exceptions for the application."""


class DomainException(Exception):
    """Base exception for all domain errors."""

    pass


class NotFoundError(DomainException):
    """Raised when a requested resource is not found."""

    pass


class ValidationError(DomainException):
    """Raised when validation fails."""

    pass


class BusinessRuleError(DomainException):
    """Raised when a business rule is violated."""

    pass
