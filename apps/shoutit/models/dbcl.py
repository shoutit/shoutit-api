from django.db import models
from apps.shoutit.models.base import UUIDModel


class CLUser(UUIDModel):
    class Meta:
        app_label = 'shoutit'

    cl_email = models.EmailField(max_length=254)