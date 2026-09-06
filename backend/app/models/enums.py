from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    PARTNER = "partner"


class LoanStatus(StrEnum):
    OPEN = "open"
    PAID = "paid"
    OVERDUE = "overdue"
    RENEGOTIATED = "renegotiated"


class InterestType(StrEnum):
    MONTHLY = "monthly"
    DAILY = "daily"
    BOTH = "both"


class NotificationStatus(StrEnum):
    UNREAD = "unread"
    READ = "read"
