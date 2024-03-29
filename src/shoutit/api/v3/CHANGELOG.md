# shoutit-api v3 changelog

## Update (2016-08-16)

### Auth Token
API sets an `auth_token={auth token}` query param for all links in notification emails. This can be used by web client to authenticate the user before viewing the target page. It is useful so the user doesn't need to manually log in coming from his email if he isn't logged in already. Auth tokens are temporary and can be used few times in short period.

### User Language
API now saves the language sent in `Accept-Language` header of the last request. This language will be used when sending notifications and emails to the user.

## Update (2016-08-01)

- Push Notifications `data` property has the `app_url` only except for incoming video calls which have caller profile properties. This was necessary as Apple only allows max payload of 2048 bytes. Check [Native Push](https://github.com/shoutit/shoutit-api/wiki/Native-Push)
- `is_sold`, `available_count` and `expires_at` are added to **Shout**. They can be used for both Offers and Requests depending on the context. 
  - `is_sold` would determine whether the Shout is sold if it is an offer or whether it is fulfilled if it is a request
  - `available_count` would determine how many pieces available when the shout is an offer or how many pieces required when it is a request
  - Shouts normally expire after 60 days from the day they published at. This allows shout owners to modify this period

## Facebook Pages (2016-07-12)

Shoutit Profiles can now link their Facebook Page in addition to their Facebook account. Check the updated wiki article [Linked Accounts](https://github.com/shoutit/shoutit-api/wiki/Linked-Accounts)

- Added `POST: /profiles/{username}/facebook_page` and `DELETE: /profiles/{username}/facebook_page` to link and unlike Facebook Pages
- Now returning `facebook_page` under `linked_accounts` property of **Detailed Profile**
- Added `name` to `linked_accounts.facebook` property of **Detailed Profile**

## Update (2016-07-11)

- API now sends emails about few notifications like new message, new listen and new credit transaction
- `name` of User objects is now truncated not to show the full `last_name` e.g. "John Doe" will be returned as "John Do." The `last_name` is still being fully saved.
- Unlinking accounts now gives an error if the profile has no password set and no other linked accounts
- API now tries to generate better usernames using the provided first and last names


## Pages Verification and Notifications (2016-07-10)

- Page admins can now verify their businesses. More on that here [Pages Verification](https://github.com/shoutit/shoutit-api/wiki/Pages#pages-verification)
- Page admins now receives notifications about activities related to their pages. Clients should subscribe to the correct notification channels as described in [Pages Notifications](https://github.com/shoutit/shoutit-api/wiki/Pages-Notifications)


## Update (2016-07-08)

- Added `/shouts/{id}/like` which allows a profile to like a shout. Shout owner will be notified
- Added `/shouts/{id}/bookmark` which allows a profile to bookmark a shout to come to it later. Shout owner won't be notified
- Added `/profiles/{username}/bookmarks` which returns a list of bookmarked shouts. Profiles can get their own bookmarked shouts only not those for other profiles
- Now returning **PageDetail** object in profile endpoints `GET /profiles/{username}` and `PATCH /profiles/{username}` Check its properties in [Shoutit Pages](https://github.com/shoutit/shoutit-api/wiki/Pages) wiki article
- Filter values for **Category** and **Shout** have now an `id` which should be passed when creating and editing shouts. More on that in [Filters](https://github.com/shoutit/shoutit-api/wiki/Filters)


## Update (2016-06-27)

- `pages` and `admins` in **DetailedProfile** are now empty lists. The endpoints `/profiles/{username}/pages` and `/pages/{username}/admins` can be used instead.
- Added `admin` property to **DetailedProfile** when it is of type `page`. This has a DetailedProfile of the currently logged in admin if any.


## Update (2016-06-26) 

### Internationalization
API now returns localized responses based on client request's `Accept-Language` header.

- Added `slug` to Tag object. Clients should start using the Tag `slug` instead of its `name` in all Tag endpoints. e.g Tag retrieve endpoint is now `/tags/{slug}`. The `name` will be a localized string that should be used only for display

### Shoutit Pages
More about the features and endpoints can be found on this wiki article [Shoutit Pages](https://github.com/shoutit/shoutit-api/wiki/Pages)

### Shoutit Credit and Social additions
Introducing Shoutit Credit system. more about it can be found on this wiki article [Shoutit Credit](https://github.com/shoutit/shoutit-api/wiki/Shoutit-Credit)

- Added `PATCH /profiles/{username}/contacts` to allow users to upload their address book. [Profile Contacts](https://dev.api.shoutit.com/docs/#!/profiles/Profile_contacts) on live docs
- Added `GET /profiles/{username}/mutual_contacts` which lists the mutual contacts that use Shoutit
- Added `GET /profiles/{username}/mutual_friends` which lists the mutual Facebook friends that use Shoutit

### Other Changes
- Shared shouts on Facebook using Prod API will be explicitly shared i.e they will appear on both Timeline and News Feed.
- Sharing on Facebook using DEV API is now possible. Shared shouts should appear on the Facebook user Activity Log. They won't be shown on his Timeline or News Feed.
- Added `total_unread_count` to Profile `stats`. This is useful for iOS clients to set the app badge
- Moved `location` from **Detailed Profile** to **Profile** This is useful when listing pages to display their location information
- Now sending `conversation_update` on new messages. This helps clients to update the list of conversations when the user is on My Chats or Public Chats screens
- Mixpanel People records are being created for profiles
- Shout owners can open / edit / delete their expired shouts
- Added `birthday` and `gender` fields to **Detailed Profile**

### Deprecations
- Moved `app_url` and `web_url` in **Notification** out of `display` to be more consistent inside native push. Check [Profile Notifications](https://github.com/shoutit/shoutit-api/wiki/Profile-Notifications)
- `missed_video_call` push events is now under `new_notification` and will appear in Profile notifications list. Check [Native Push](https://github.com/shoutit/shoutit-api/wiki/Native-Push)
- Conversation objects in `GET /conversations` and `GET /public_chats` are of type **Conversation** and not **Detailed Conversation**. They don't include `profiles` or `about`. This can be retrieved from `GET /conversations/{id}`
- Removed `subject` and `icon` from **Detailed Conversation**. They are *write only* properties used only when creating a Public Chat conversation


## Conversation (2016-05-20)

- Updated [Messaging Wiki](https://github.com/shoutit/shoutit-api/wiki/Intro-to-Messaging)
- Divided Conversation to **Conversation** and **Conversation Detail**. The earlier will be returned in all endpoints while the later will be only returned in conversation detail endpoint `GET /conversations/{id}`
- Clients should utilize the Conversation object and only when opening the chat ask for Conversation Detail
- Clients should listen to `conversation_update` rather than asking for conversation detail after every admin action
- Add `app_url` to **Message** object this can be used to open the conversation from Native Push

### To be deprecated
- At the moment all endpoints will keep returning full **Conversation Detail** objects until all clients are updated to utilize regular **Conversation** objects

## Update (2016-05-19)

- Accept `location` and return property when creating / listing Public Chats
- Ignore reading own messages
- Added `app_url` to **Profile**, **Conversation**, **Shout** and **DiscoverItem**

## Update (2016-05-17)

- Introducing **MiniProfile** which has `id`, `username` and `name`. This will be used in endpoints that don't require extra profile properties
- Added `last_message_summary` in Conversation `display`. This can be used to display the text under title and sub_title
- Added `attachments_count` which has number of attached `shout`s, `media`s, `profile`s and `location`s. It will be returned only in detail Conversation endpoint `/conversations/{id}`
- Added `creator` to Conversation. It is of type MiniProfile

### To be deprecated
- `last_message` from Conversation
- `about` and `profiles` will be only returned in detail Conversation endpoint `/conversations/{id}` and not the main `/conversations/`
- `subject` and `icon` in Conversation will not returned and only used when creating the Conversation (public chat)


## Update (2016-05-13)

- Now returning `new_listeners_count` when listening / stop listening to profiles and tags
- Added `is_expired` property to Shout
- Added `exclude` parameter to `GET /shouts`. It can be either shout id or comma separated shout ids. This is useful when getting other owner shouts on his shout details page not to show the shout again


## Chat actions (2016-05-12)

- Updated the following actions docs
  - `POST /conversations/{id}/add_profile` 
  - `POST /conversations/{id}/remove_profile` 
  - `POST /conversations/{id}/promote_admin` 
  - `POST /conversations/{id}/block_profile` 
  - `POST /conversations/{id}/unblock_profile` 
- Added `PATCH /conversations/{id}` that allows conversation admins to update `subject` and `icon` of the conversation
- Now returning `display` property in each conversation. It includes `title`, `sub_title` and `image` which can be used to display the conversation
- When creating public chat, a message is being auto created and added to the conversation "Profile created this public chat"
- Added `blocked` property to Conversation that includes the ids of blocked profiles
- Added `GET /conversations/{id}/blocked` that returns a list of blocked profiles from this conversation
- Conversations (from type `public_chats`) can be now reported using `POST /misc/reports`
- Allow attaching profiles in messages. Check [Message Attachment](https://github.com/shoutit/shoutit-api/wiki/Intro-to-Messaging#message-attachment)
- Added `/conversation/{id}/media` to list media attachments (images and videos)
- Added `/conversation/{id}/shouts` to list shout attachments


## Update (2016-05-10)

### Public Chats

- Added `GET /public_chats` which is a shortcut to `GET /conversations?type=public_chat`
- Added `POST /public_chats` which is a shortcut to `POST /conversations` with `type` set to `public_chat` in the request body
- Check [Public Chats wiki article](https://github.com/shoutit/shoutit-api/wiki/Public-Chats) for more info

### Listening / Listeners / Interests

- Added `/profiles/{username}/interests` which returns a list of profile interests (tags)
- Removed the `type` parameter from `/profiles/{username}/listening` it now returns a mixed list of Profiles (Users and Pages)


## Deprecations (2016-04-01)

- Removed `user` and `users` from all v3 endpoints except those for authentication are now pending deprecation
- Removed `main_tag` from Category object
- Removed `/misc/categories` and `/misc/shout_sort_types`
- Added `/shouts/categories` and `/shouts/sort_types`


## Video Chat and Stats (2016-03-31)

- Enhanced the Video chatting flow. Check [Video Chat wiki](https://github.com/shoutit/shoutit-api/wiki/Video-Chat).
- Added `stats` to Profile object. Check [Profiles wiki](https://github.com/shoutit/shoutit-api/wiki/Intro-to-Profiles) for information on how to use it.


## Push (2016-03-30)

Check the latest [Notifications wiki](https://github.com/shoutit/shoutit-api/wiki/Notifications#push-and-pusher).

- Pusher channel names in v3 should include the version e.g `presence-v3-c-conversationid`
- Profile channel name is now uses `p` instead of `u` i.e. `presence-v3-p-profileid`
- Added new push events: `new_read_by`, `profile_update`, and `conversation_update`
- Check the new Pusher credentials for development in the wiki.
- Added `/messages/{id}/read` endpoint to mark messages as read / unread


## Dev (2016-03-29)

- `type` is now required query parameter when retrieving list of listening on `/profiles/{username}/listening`
- Added `type` property to **MessageAttachment** which can be either `shout`, `location` or `media`
    - `shout` attachment has `shout` property
    - `location` attachment has `location` property
    - `media` attachment has `images` and `videos` properties
- Unified the inputs and outputs of empty string values according to the following

### Profile
on `PATCH: /profiles/{id}`

- `image`, `cover`, `mobile`, `gender`, `bio` / `about`, `video`, `website`
    - input: not set, empty `""` or `null`
    - output: `null`
- `push_tokens.apns`, `push_tokens.gcm`
    - input: `null`
    - output: `null`
  
### Shout
on `POST: /shouts` and `PATCH: /shouts/{id}`

- `title`, `text`, `mobile`
    - input: not set, empty `""` or `null`
    - output: `null`
- `mobile_hint`
    - output: `null`
    
### Message and Report
on `POST: /conversations/{id}/reply`, `POST: /shouts/{id}/reply` and `POST: /profiles/{id}/chat`

- `text`
    - input: not set, empty `""` or `null`
    - output: `null`

### Report
on `POST: /misc/reports`

- `text`
    - input: not set, empty `""` or `null`
    - output: `null`


## New Error responses (2016-03-25)

V3 of the API is now returning a standard error responses according to this [wiki page](https://github.com/shoutit/shoutit-api/wiki/Error-Responses)


## Update (2016-03-21)

- Added `conversation/{id}`
- Added `conversation` to **Profile** object. This helps identifying if there was a previous conversation between the caller and the requested profile
- Added `/shouts/autocomplete` endpoint. Check live docs: [Shouts Autocomplete](https://dev.api.shoutit.com/docs/#!/shouts/Shout_autocomplete)
- Added `read_by` to **Message** objects
- Started only accepting `application/json` as `contente_type` in requests headers to all endpoints unless explicitly stated otherwise
- Added `Cache-Control` headers to `/shouts/categories`, `/shouts/sort_types` and `/misc/currencies` endpoints


## Initial commits (2016-02-22)

- Live documentation: http://dev.api.shoutit.com/docs/
- V3 base url: `http://dev.api.shoutit.com/v3`

### OAuth2

- Changed `shoutit_signin` to `shoutit_login`
- Added `shoutit_guest` grant type to [OAuth2 endpoint](https://dev.api.shoutit.com/docs/#!/oauth2) (notice the returned `GuestUser` object)

### Profiles

**Profile** is the base account for _Users_ and _Pages_. Profile has `type` property which can be either `user` or `page`. All previous **User** endpoints are ported to similar Profile endpoints

- `/profiles`

###Users

- Removed `/users/{USERNAME}/shouts` use `/shouts?profile={USERNAME}` instead
- For each endpoint that has `user` or `users` there is respective and totally equal `profile` or `profiles`. The later properties are pending deprecation and clients should use the new ones

###Tags

- Removed `/tags/{TAGNAME}/shouts` use `/shouts?tags={TAGNAME}` instead

###Discover

- Removed `/discover/{DISCOVER_ID}/shouts` use `/shouts?discover={DISCOVER_ID}` instead

###Shouts

- Removed `tags` property from **Shout** object and replaced it with `filters`
- `filters` is a list of **Filter** objects
- **Shout Filter** is an object used to describe the shouts in more details
```
{
    "name": "Disk Size",
    "slug": "disk_size",
    "value": {
        "name": "500 GB",
        "slug": "500_gb"
    }
}
```
- `price` is now a big integer field and deals with *cents*
- Added categories endpoint `/shouts/categories` which along with the categories it returns `filters` property. The only difference between **Shout Filter** and **Category Filter** is that category filters have `values` instead of `value`. This helps when creating or editing shouts, also when filtering the search by passing those as query parameters

**Category example**
```
{
    "name": "Cars & Motors",
    "slug": "cars-motors",
    "icon": "https://tag-image.static.shoutit.com/categories/cars-i.png,
    "image": "https://tag-image.static.shoutit.com/bb4f3137-48f2-4c86-89b8-0635ed6d426e-cars-motors.jpg,
    "filters": [
        {
            "name": "Engine",
            "slug": "engine",
            "values": [
                {
                    "name": "V6",
                    "slug": "v6"
                },
                {
                    "name": "V8",
                    "slug": "v8"
                }
            ]
        }
    ]
}
```

- Added `available_count` and `is_sold` to Shout object. They can be set when creating or updating shouts and should be only used with offers
- Added `mobile` which can be set when creating or updating shouts. Returned shouts don't have it and clients should ask for it using `/shouts/{id}/call`
- Added `mobile_hint` and `is_mobile_set`
	- Mobile apps should display the Call button when `is_mobile_set` is true
	- Webapp can use the `mobile_hint` to display part of the mobile
	- When the user wants to view (on webapp) or call (on mobile apps), the clients should request `mobile` using `/shouts/{id}/call`
	- Added `/shouts/{id}/call` which returns the `mobile` of that shout to contact its owner

###Creating and editing Shouts

Check the live docs: [Shout create](http://dev.api.shoutit.com/docs/#!/shouts/Shout_create), [Shout update](http://dev.api.shoutit.com/docs/#!/shouts/Shout_partial_update)

- All attributes are now optional when creating a shout except `type`, however only these cases are considered valid:
	- Offer with either one of the following: `title`, `images` or `videos`
	- Request with a `title`
- Setting the category can be only done using its slug. Either:
	- directly i.e. `"category": "car-motors"`
	- passing the entire category object which has `slug` in it
- Empty fields should be passed as `null`

###Search

- Categories should be passed as slugs i.e. `category=cars-motors`

###Misc

- Removed `google_geocode_response` from `location` objects and stopped accepting it as a valid location. clients should pass `latitude` and `longitude` to represent a location
- Deprecated the misc endpoint `/misc/parse_google_geocode_response`

###Pending deprecation

- `/misc/categories`, use `/shouts/categories` instead
- `main_tag` property of a category, the category `slug` can be used to know the main tag as they are identical
- Remove `user` and `users` properties from all endpoints in favor of `profile` and `profiles` respectively. This also applies on receiving objects. Clients should use the profile attributes. This will make sure no confusion about profiles, users and pages in the future. For more information check [Profiles wiki](https://github.com/shoutit/shoutit-api/wiki/Profiles)
