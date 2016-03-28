# shoutit-api v3 changelog

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
