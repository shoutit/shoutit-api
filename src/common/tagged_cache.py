from django.core.cache import cache as django_cache


class TaggedCache(object):

    cache = django_cache
    tags_dict = {}

    def get_tags_dict(self):
        result = self.get("tags_dict")
        if not result:
            result = {}
            self.update_tags_dict(result)
        return result

    def update_tags_dict(self, tags_dict=None):
        tags_dict = {} if tags_dict is None else tags_dict
        self.set("tags_dict", tags_dict)

    def set_tag_keys(self, tag, keys):
        tags_dict = self.get_tags_dict()
        tags_dict[tag] = keys
        self.update_tags_dict(tags_dict)

    def append_key_to_tag(self, tag, key):
        tags_dict = self.get_tags_dict()
        tags_dict[tag].append(key)
        self.update_tags_dict(tags_dict)

    def set_with_tags(self, key, value, tags, timeout):
        def add(_tag):
            self.set_tag_keys(_tag, [])
        tags_dict = self.get_tags_dict()
        [add(tag) for tag in tags if tag not in tags_dict]
        tags_dict = self.get_tags_dict()
        [tags_dict[tag].append(key) for tag in tags if key not in tags_dict[tag]]
        self.update_tags_dict(tags_dict)
        self.set(key, value, timeout)

    def get_by_tag(self, tag):
        tags_dict = self.get_tags_dict()
        keys = tags_dict[tag]
        keys_to_delete = []
        result = {}
        for key in keys:
            if key in self:
                result[key] = self.get(key)
            else:
                keys_to_delete.append(key)
        [tags_dict[tag].remove(key) for key in keys_to_delete]
        self.update_tags_dict(tags_dict)
        return result

    def delete_by_tag(self, tag):
        tags_dict = self.get_tags_dict()
        if tag not in tags_dict:
            tags_dict[tag] = []
            self.update_tags_dict(tags_dict)
        keys_to_delete = []

        def deferred_delete(_key):
            self.delete(_key)
            keys_to_delete.append(_key)

        [deferred_delete(key) for key in tags_dict[tag]]
        [tags_dict[tag].remove(key) for key in keys_to_delete]
        self.update_tags_dict(tags_dict)

    def get_perma(self, request, key):
        if request.user.is_authenticated():
            return TaggedCache.get('perma|%s|%s' % (key, request.user.pk))
        elif hasattr(request, 'session'):
            return TaggedCache.get('perma|%s|%s' % (key, request.session.session_key))
        else:
            return None

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value, timeout=None, version=None):
        self.cache.set(key, value, timeout, version)

    def delete(self, key):
        self.cache.delete(key)

    def __contains__(self, key):
        return key in self.cache

TaggedCache = TaggedCache()