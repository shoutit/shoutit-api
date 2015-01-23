from behave import *

use_step_matcher("re")

@when("user clicks on the search icon")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@step("user enters a search term")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@step("search term matches a user's name")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@then("user profile is returned")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass