# Created by Muaaz at 1/12/2015
  @Authentication
Feature: user sign in

  Scenario: shoutit sign in
    Given user has a shoutit account
    And user enters a valid email address
    And user enters a valid password
    Then user is granted access

  Scenario: g+ sign in
    Given user has a google account
    And user agrees to let shoutit use it's basic info
    And user lets shoutit use his/her G+ for sign in
    And user agrees to let shoutit upload videos to his YouTube account
    Then user is granted access

  Scenario: facebook sign in
    Given user has a Facebook account
    And user agrees that shoutit view his/her email address
    And user agrees that shoutit view his/her birthday
    And user allows shoutit to publish on his behalf
    Then user is granted access