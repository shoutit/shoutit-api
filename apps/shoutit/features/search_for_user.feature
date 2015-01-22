# Created by Muaaz at 1/22/2015
  @users
Feature: search for user
  user searching for another user's profile

  Scenario: search for user
    Given user is logged in
    And user is connected to the internet
    When user clicks on the search icon
    And user enters a search term
    And search term matches a user's name
    Then user profile is returned