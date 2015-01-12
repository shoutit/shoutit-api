# Created by Muaaz at 1/12/2015
Feature: new user sign up
  user signs up to create a new shoutit account

  Scenario: new user sign up for shoutit account
    Given user has no shoutit account
    And user has a valid email address
    And user wants to sign up with his email address
    When user enters a user name
    And user enters a first name
    And user enters a last name
    And user enters a valid email address
    And user repeats email address
    And user enters a valid password
    And user repeats a matching password
    Then new account is created for the user
    And user is granted access

  Scenario: new user sing in with G+
    user doesn't want to create a shoutit account but signs in with a G+ account
    Given user has a google account
    And user agrees to let shoutit use it's basic info
    And user lets shoutit use his/her G+ for sign in
    And user agrees to let shoutit upload videos to his YouTube account
    Then user is granted access

  Scenario: New user sign in with Facebook
    user doesn't want to create a shoutit account but signs in with a Facebook account
    Given user has a Facebook account
    And user agrees that shoutit view his/her email address
    And user agrees that shoutit view his/her birthday
    And user allows shoutit to publish on his behalf
    Then user is granted access