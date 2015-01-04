# Created by muaazo at 12.12.14
Feature: Signup
  grant access to shoutit

  Scenario: User opens the application for the first time
    Given user installed the application
    And Application is running
    When user authenticated
    Then access token is returned