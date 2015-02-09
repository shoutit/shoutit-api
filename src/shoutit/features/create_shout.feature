# Created by Muaaz at 1/12/2015
  @shouts
Feature: create new shout
  user creates a new shout to post to shoutit

  Scenario: create an offer while logged in with shoutit account
    Given user is logged in with shoutit account
    And user is not connected to facebook
    And user is not connected to g+
    And user choose offer
    When user click on new shout
    And enters a shout title
    And enters a shout description
    And enters at least one tag
    And enters a price
    And choose a currency
    And uploads at least one image
    And clicks shoutit
    Then shout is created as an offer

  Scenario: create a request while logged in with shoutit account
    Given user is logged in with shoutit account
    And user is not connected to facebook
    And user is not connected to g+
    And user choose request
    When user click on new shout
    And enters a shout title
    And enters a shout description
    And enters at least one tag
    And enters a price
    And choose a currency
    And uploads at least one image
    And clicks shoutit
    Then shout is created as a request

  Scenario: create an offer while logged in with g+
    Given user is logged in with g+
    And user choose offer
    When user click on new shout
    And enters a shout title
    And enters a shout description
    And enters at least one tag
    And enters a price
    And choose a currency
    And user uploads at least one image if video is not uploaded
    And user uploads a video
    And clicks shoutit
    Then shout is created as an offer

  Scenario: create a request while logged in with g+
    Given user is logged in with g+
    And user choose request
    When user click on new shout
    And enters a shout title
    And enters a shout description
    And enters at least one tag
    And enters a price
    And choose a currency
    And user uploads at least one image if video is not uploaded
    And user uploads a video
    And clicks shoutit
    Then shout is created as a request

  Scenario: create an offer while logged in with facebook
    Given user is logged in with facebook
    And user choose offer
    When user click on new shout
    And enters a shout title
    And enters a shout description
    And enters at least one tag
    And enters a price
    And choose a currency
    And user uploads at least one image if video is not uploaded
    And user uploads a video
    And clicks shoutit
    Then shout is created as an offer

  Scenario: create a request while logged in with facebook
    Given user is logged in with facebook
    And user choose request
    When user click on new shout
    And enters a shout title
    And enters a shout description
    And enters at least one tag
    And enters a price
    And choose a currency
    And user uploads at least one image if video is not uploaded
    And user uploads a video
    And clicks shoutit
    Then shout is created as a request