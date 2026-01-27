from .base import DEBUG

if DEBUG:
    from .dev import *
else:
    from .prod import *