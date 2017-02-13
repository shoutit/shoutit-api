from common.constants import Constant


class CRMSourceType(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


CRM_SOURCE_XML_LINK = CRMSourceType("XML Link")


class XMLLinkCRMSourceStatus(Constant):
    counter, values, texts, choices = 0, {}, {}, ()


XML_LINK_DISABLED = XMLLinkCRMSourceStatus("Disabled")
XML_LINK_WAITING_APPROVAL = XMLLinkCRMSourceStatus("Waiting Approval")
XML_LINK_FETCHING = XMLLinkCRMSourceStatus("Fetching")
XML_LINK_ENABLED = XMLLinkCRMSourceStatus("Enabled")
XML_LINK_BLOCKED = XMLLinkCRMSourceStatus("Blocked")
