# -*- coding: utf-8 -*-
"""

"""
from django.core.management.base import BaseCommand
from django.db.models import Q
import re
import requests
from rest_framework.exceptions import ValidationError
from shoutit.api.v2.serializers import ShoutDetailSerializer
from shoutit.models import Shout, ShoutIndex
from shoutit.utils import debug_logger
from shoutit_crm.constants import XML_LINK_ENABLED
from shoutit_crm.models import XMLLinkCRMSource, XMLCRMShout
import xmltodict
from html.parser import HTMLParser


class Command(BaseCommand):
    help = 'Import shouts from XML CRM sources.'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--count', default=10, type=int)

    def handle(self, *args, **options):
        # Get XML CRM Sources
        count = options['count']
        xml_crm_sources = XMLLinkCRMSource.objects.filter(status=XML_LINK_ENABLED)
        processed_sources = []
        errors = []

        # Load XML from source
        for source in xml_crm_sources:
            try:
                self.process_source(source, count)
                processed_sources.append(source)
            except Exception as e:
                errors.append(e)
                debug_logger.error("Error processing source: %s" % str(source))
                debug_logger.error(str(e))

        debug_logger.info("Successfully processed %s sources" % len(processed_sources))
        if len(errors):
            debug_logger.error("Encountered %s errors" % len(errors))

    def process_source(self, source, count):
        # load source xml
        xml = self.xml_from_source(source)

        # Parse XML
        data = xmltodict.parse(xml)

        # Map data
        mapping = source.mapping
        raw_shouts = (map_data(data, mapping) or [])[:count]

        # Collect crm ids
        source_ids = [rs.get('id_on_source') for rs in raw_shouts]

        # Disable current source Shouts with no matching crm ids
        current_crm_shouts = source.crm_shouts.filter(shout__is_disabled=False)
        discarded_crm_shouts = current_crm_shouts.filter(~Q(id_on_source__in=source_ids))
        discarded_shouts_ids = [str(d_crm_s.shout_id) for d_crm_s in discarded_crm_shouts]
        Shout.objects.filter(id__in=discarded_shouts_ids).update(is_disabled=True)
        # Remove them from the index too
        ShoutIndex()._get_connection().delete_by_query(index=ShoutIndex()._get_index(),
                                                       body={"query": {"terms": {"_id": discarded_shouts_ids}}})

        # Create or update Shouts
        for raw_shout in raw_shouts:
            id_on_source = raw_shout.get('id_on_source')
            try:
                crm_shout = XMLCRMShout.objects.get(id_on_source=id_on_source)
                op = 'updated'
            except XMLCRMShout.DoesNotExist:
                crm_shout = None
                op = 'created'
            finally:
                shout = crm_shout.shout if crm_shout else None
            try:
                if shout:
                    if shout.images:
                        raw_shout['images'] = shout.images
                    shout.is_disabled = False
                raw_shout['text'] = text_from_html(raw_shout['text'])
                serializer = ShoutDetailSerializer(instance=shout, data=raw_shout, context={'user': source.user})
                serializer.is_valid(raise_exception=True)
                shout = serializer.save()
                if not crm_shout:
                    crm_shout = XMLCRMShout.create(attached_object=source, id_on_source=id_on_source, shout=shout, xml_data="test")
                debug_logger.info("Listing %s was %s successfully" % (id_on_source, op))
            except ValidationError as e:
                debug_logger.error("Listing %s has the following errors %s" % (id_on_source, str(e)))

    def xml_from_source(self, source):
        # Used for testing only. could be used again.
        # path = "D:\\dev\crm_example.xml"
        # with open(path, "r") as xml_file:
        #     xml_data = xml_file.read().replace('\n', '')
        xml_data = requests.get(source.url).content.decode()
        return xml_data


def map_data(data, mapping):
    mapped_data = None
    data_type = mapping.get('type')
    if data_type == 'list':
        mapped_data = _map_list(data, mapping)
    elif data_type == 'dict':
        mapped_data = _map_dict(data, mapping)
    elif data_type == 'str':
        mapped_data = _map_str(data, mapping)
    elif data_type == 'float':
        mapped_data = _map_float(data, mapping)
    return mapped_data


def _map_float(data, mapping):
    mapped_float = 0
    if isinstance(data, str):
        mapped_float = data
    elif isinstance(data, dict):
        mapped_float = mapping.get('value', 0)
        node = mapping.get('node')
        if node:
            mapped_float = data.get(node)
    return float(mapped_float)


def _map_str(data, mapping):
    mapped_str = ''
    node = mapping.get('node')
    str_map = mapping.get('map')
    str_re = mapping.get('re')
    str_pre = mapping.get('pre', '')
    str_post = mapping.get('post', '')
    str_extra_lines = mapping.get('extra_lines', [])
    blank_concat = mapping.get('blank_concat', True)

    if isinstance(data, str):
        mapped_str = data
    elif isinstance(data, dict):
        mapped_str = mapping.get('value') or ''
        if node:
            mapped_str = data.get(node) or ''

    # Extract using regular expression
    if str_re:
        try:
            mapped_str = re.search(str_re, mapped_str).groups()[0]
        except Exception:
            pass

    # Map the str using the given dict
    if str_map:
        mapped_str = str_map.get(mapped_str)

    # Concatenate with pre and post
    if mapped_str or blank_concat:
        mapped_str = str_pre + mapped_str + str_post

    # Add extra lines
    for extra_line_map in str_extra_lines:
        mapped_extra_line = map_data(data, extra_line_map)
        mapped_str = "%s<br/>%s" % (mapped_str, mapped_extra_line)
    return mapped_str


def _map_dict(data, mapping):
    mapped_dict = {}
    attributes = mapping.get('attributes', {})
    for attr_name, attr_mapping in attributes.items():
        mapped_dict[attr_name] = map_data(data, attr_mapping)
    return mapped_dict


def _map_list(data, mapping):
    mapped_list = []
    node = mapping.get('node')
    item_mapping = mapping.get('item')
    items_mapping = mapping.get('items', [])
    drop_empty = mapping.get('drop_empty', True)

    # List with single item mapping for all its children
    if node and item_mapping:
        items = data.get(node, {}).get(item_mapping.get('node', ''), [])
        # In the case of only one item
        if not isinstance(items, list):
            items = [items]
        for item in items:
            mapped_item = map_data(item, item_mapping)
            mapped_list.append(mapped_item)

    # List with different mapping for each child
    elif items_mapping:
        for _item_mapping in items_mapping:
            mapped_item = map_data(data, _item_mapping)
            mapped_list.append(mapped_item)

    if drop_empty:
        mapped_list = [m for m in mapped_list if m]
    return mapped_list


class DeHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.__text = []

    def handle_data(self, data):
        text = data.strip()
        if len(text) > 0:
            text = re.sub('[ \t\r\n]+', ' ', text)
            self.__text.append(text + ' ')

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.__text.append('\n\n')
        elif tag == 'br':
            self.__text.append('\n')

    def handle_startendtag(self, tag, attrs):
        if tag == 'br':
            self.__text.append('\n')

    def text(self):
        return ''.join(self.__text).strip()


def text_from_html(text):
    try:
        parser = DeHTMLParser()
        parser.feed(text)
        parser.close()
        return parser.text()
    except:
        return text
