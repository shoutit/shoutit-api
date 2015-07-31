import os
import requests
try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse
import hashlib


class MailChimpException(Exception):
    def __init__(self, message, response=None):
        # Call the base class constructor with the parameters it needs
        super(MailChimpException, self).__init__(message)
        self.response = response
        if response is not None:
            try:
                self.json = response.json()
            except ValueError:
                self.html = response.content

    def __str__(self):
        if self.response is not None:
            if hasattr(self, 'json'):
                return "%s\n%s" % (self.message, str(self.json))
            else:
                return "%s\n%s" % (self.message, self.html)
        else:
            return "%s" % self.message


def find_credentials():
    """
    Look in the current environment for MAilChimp credentials
    """
    try:
        key = os.environ["MAILCHIMP_API_KEY"]
        return key
    except KeyError:
        return None


class Client(object):
    def __init__(self, api_key=None, host="api.mailchimp.com", api_version="3.0", verify=True):
        """
        Create SMSGlobal API client.
        """

        # Get account credentials
        if not api_key:
            api_key = find_credentials()
            if not api_key:
                raise MailChimpException("Could not find an API KEY")
        parts = api_key.split('-')
        if len(parts) != 2:
            raise MailChimpException("This doesn't look like an API Key: %s\nThe API Key should have both a key "
                                     "and a server name, separated by a dash, like this: abcdefg8abcdefg6abcdefg4-us1")
        self.api_key = api_key
        self.shard = parts[1]
        self.host = host
        self.api_version = api_version
        self.api_root = "https://%s.%s/%s/" % (self.shard, self.host, self.api_version)
        self.verify = verify

    def get_member(self, list_id, email):
        hashed_email = hashlib.md5(email).hexdigest()
        return self.get('lists/%s/members/%s' % (list_id, hashed_email))

    def delete_member(self, list_id, email):
        hashed_email = hashlib.md5(email).hexdigest()
        return self.delete('lists/%s/members/%s' % (list_id, hashed_email))

    def add_member(self, list_id, email, status, extra_fields=None, merge_fields=None):
        member = {
            "email_address": email,
            "status": status,
        }
        if extra_fields:
            member.update(extra_fields)
        if merge_fields:
            member.update({"merge_fields": merge_fields})
        return self.post('lists/%s/members/' % list_id, json=member)

    def get(self, path, params=None):
        return self.request('GET', path, params=params)

    def post(self, path, json):
        return self.request('POST', path, json=json)

    def patch(self, path, json=None):
        return self.request('PATCH', path, json=json)

    def delete(self, path):
        return self.request('DELETE', path)

    def request(self, method, path, params=None, json=None):
        url = urlparse.urljoin(self.api_root, path)
        auth = ('apikey', self.api_key)
        headers = {"User-Agent": "MailChimp Python Client 3.0", "Accept": "application/json"}
        try:
            response = requests.request(method, url, auth=auth, headers=headers, params=params, json=json, verify=self.verify)
        except requests.RequestException as e:
            raise MailChimpException(str(e))
        else:
            return self.parse(response)

    @staticmethod
    def parse(response):
        if 200 <= response.status_code < 300:
            return response.json() if response.status_code != 204 else ""
        else:
            raise MailChimpException(message="%s Response" % response.status_code, response=response)
