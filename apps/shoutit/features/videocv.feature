# Created by mo at 28/12/14

@posting @shout_types @video_cv @videos
Feature: Video CV
  Users will be able to post video CVs allowing employers to have an idea about them before interview.

  Scenario: post video cv (upload)
    Given user is logged in
    And user is connected to the internet
    And user is viewing his/her own profile
    And user clicks on upload video cv
    And user clicks on upload video
    And user uploads a 30 seconds video
    Then video cv is created

  Scenario: post video cv (record)
    Given user is logged in
    And user is connected to the internet
    And user is viewing his/her own profile
    And user clicks on record a video
    Then a video recorder diagram shows and allows the user to record a 30 seconds video
    And video cv is created

  Scenario: edit video cv (upload)
    Given user is logged in
    And user is connected to the internet
    And user is viewing his/her own profile
    And user has already uploaded a video cv
    And user clicks on edit video cv
    And user clicks on upload video cv
    And user uploads a 30 seconds video
    Then video cv is edited

  Scenario: edit video cv (record)
    Given user is logged in
    And user is connected to the internet
    And user is viewing his/her own profile
    And user has already uploaded a video cv
    And user clicks on edit video cv
    And user clicks on record a video
    Then a video recorder diagram shows and allows the user to record a 30 seconds video
    And video cv is edited