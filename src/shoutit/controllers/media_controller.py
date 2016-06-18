"""

"""
from __future__ import unicode_literals

import uuid
from cStringIO import StringIO

import boto
import requests
from PIL import Image
from django.conf import settings
from django.utils import timezone
from django_rq import job

from shoutit.utils import error_logger, debug_logger


class ImageData(str):
    def __repr__(self):
        return "ImageData: %d bytes" % len(self)


def generate_image_name():
    return "%s-%s.jpg" % (str(uuid.uuid4()), int(timezone.now()))


def set_profile_media(profile, attr, url=None, data=None):
    if data:
        data = ImageData(data)
    return _set_profile_media.delay(profile, attr, url, data)


@job(settings.RQ_QUEUE)
def _set_profile_media(profile, attr, url=None, data=None):
    bucket_name = 'shoutit-user-image-original'
    public_url = 'https://user-image.static.shoutit.com'
    file_name = '%s_%s.jpg' % (profile.pk, attr)
    s3_url = upload_image_to_s3(bucket_name, public_url, url=url, data=data, filename=file_name)
    if s3_url:
        setattr(profile, attr, s3_url)
        profile.save(update_fields=[attr])


def upload_image_to_s3(bucket_name, public_url, url=None, data=None, filename=None, raise_exception=False):
    assert url or data, 'Must pass url or data'
    source = url if url else str(ImageData(data))
    debug_logger.debug("Uploading image to S3 from %s" % source)
    try:
        if not data:
            response = requests.get(url, timeout=10)
            data = response.content
        if not filename:
            filename = generate_image_name()
        # Check if an actual image
        Image.open(StringIO(data))
        # Connect to S3
        s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
        bucket = s3.get_bucket(bucket_name)
        key = bucket.new_key(filename)
        key.set_metadata('Content-Type', 'image/jpg')
        # Upload
        key.set_contents_from_string(data)
        # Construct public url
        s3_image_url = '%s/%s' % (public_url, filename)
        return s3_image_url
    except Exception:
        if raise_exception:
            raise
        else:
            error_logger.warn("Uploading image to S3 failed", exc_info=True)