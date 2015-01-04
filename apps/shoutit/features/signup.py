from behave import *

use_step_matcher("re")

@given("user installed the application")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@step("Application is running")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@when("user authenticated")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@then("access token is returned")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass