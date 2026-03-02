from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonBurstThrottle(AnonRateThrottle):
    rate = "20/min"


class UserBurstThrottle(UserRateThrottle):
    rate = "100/min"
