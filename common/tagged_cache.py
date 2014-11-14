from django.core.cache import cache


class TaggedCache(object):

    @staticmethod
    def get_tags_dict():
        result = TaggedCache.get("tags_dict")
        if not result:
            result = {}
            TaggedCache.update_tags_dict(result)
        return result

    @staticmethod
    def update_tags_dict(tags_dict={}):
        TaggedCache.set("tags_dict", tags_dict)

    @staticmethod
    def set_tag_keys(tag, keys):
        tags_dict = TaggedCache.get_tags_dict()
        tags_dict[tag] = keys
        TaggedCache.update_tags_dict(tags_dict)

    @staticmethod
    def append_key_to_tag(tag, key):
        tags_dict = TaggedCache.get_tags_dict()
        tags_dict[tag].append(key)
        TaggedCache.update_tags_dict(tags_dict)

    @staticmethod
    def set_with_tags(key, value, tags, timeout):
        def add(tag):
            TaggedCache.set_tag_keys(tag, [])
        tags_dict = TaggedCache.get_tags_dict()
        [add(tag) for tag in tags if not tags_dict.has_key(tag)]
        tags_dict = TaggedCache.get_tags_dict()
        [tags_dict[tag].append(key) for tag in tags if key not in tags_dict[tag]]
        TaggedCache.update_tags_dict(tags_dict)
        cache.set(key, value, timeout)

    @staticmethod
    def set(key, value, timeout=None, version=None):
        cache.set(key, value, timeout, version)

    @staticmethod
    def get_by_tag(tag):
        tags_dict = TaggedCache.get_tags_dict()
        keys = tags_dict[tag]
        keys_to_delete = []
        result = {}
        for key in keys:
            if cache.has_key(key):
                result[key] = cache.get(key)
            else:
                keys_to_delete.append(key)
        [tags_dict[tag].remove(key) for key in keys_to_delete]
        TaggedCache.update_tags_dict(tags_dict)
        return result

    @staticmethod
    def get(key):
        return cache.get(key)

    @staticmethod
    def delete(key):
        cache.delete(key)

    @staticmethod
    def delete_by_tag(tag):
        tags_dict = TaggedCache.get_tags_dict()
        if not tags_dict.has_key(tag):
            tags_dict[tag] = []
            TaggedCache.update_tags_dict(tags_dict)
        keys_to_delete = []

        def deferred_delete(_key):
            cache.delete(_key)
            keys_to_delete.append(_key)

        [deferred_delete(key) for key in tags_dict[tag]]
        #[keys.remove(key) for key in keys_to_delete for keys in tags_dict.itervalues() if key in keys]
        [tags_dict[tag].remove(key) for key in keys_to_delete]
        TaggedCache.update_tags_dict(tags_dict)

    @staticmethod
    def has_key(key):
        return key in cache


    @staticmethod
    def get_perma(request, key):
        if request.user.is_authenticated():
            return TaggedCache.get('perma|%s|%d' % (key, request.user.pk))
        elif hasattr(request, 'session'):
            return TaggedCache.get('perma|%s|%s' % (key, request.session.session_key))