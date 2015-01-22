# Created by Muaaz at 1/22/2015
Feature: listening to a user
  user listens to others to get latest updates

  Scenario: listening to user to get latest updates
    Given user is logged in
    And user is connected to the internet
    And user is viewing another user's profile
    And user clicks on listen button
    Then user is listening to the user's in concern shouts
    And user can view the user's in concern shouts
    And user can message the user in concern

  Scenario: stop listening to user
    Given user is logged in
    And user is connected to the internet
    And user is viewing another user's profile
    And user clicks on stop listening button
    Then user is no longer listening to user's in concern

  Scenario: view user's listeners
    Given user is logged in
    And user is connected to the internet
    And user is viewing another user's profile
    And user clicks on listeners
    Then a list of users listening to the user in concern is returned

  Scenario: view user's listening
    Given user is logged in
    And user is connected to the internet
    And user is viewing another user's profile
    And user clicks on listening
    Then a list of users the user in concern is listening to is returned
