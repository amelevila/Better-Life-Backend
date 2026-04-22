from django.contrib import admin

from .models import BodyMetrics
from .models import UserAccount
from .models import UserProfile

admin.site.register(UserAccount)
admin.site.register(UserProfile)
admin.site.register(BodyMetrics)
