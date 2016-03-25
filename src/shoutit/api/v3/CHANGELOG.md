# shoutit-api v3 changelog



## Initial commits (2016-02-22)

- Live documentation: http://dev.api.shoutit.com/docs/
- V3 base url: `http://dev.api.shoutit.com/v3`

### OAuth2

- Changed `shoutit_signin` to `shoutit_login`
- Added `shoutit_guest` grant type to [OAuth2 endpoint](https://dev.api.shoutit.com/docs/#!/oauth2) (notice the returned `GuestUser` object)

### Profiles
**Profile** is the base account for _Users_ and _Pages_. Profile has `type` property which can be either `user` or `page`. All previous **User** endpoints are ported to similar Profile endpoints. 

- `/profiles`

###Users
- Removed `/users/{USERNAME}/shouts` use `/shouts?profile={USERNAME}` instead
- For each endpoint that has `user` or `users` there is respective and totally equal `profile` or `profiles`. The later properties are pending deprecation and clients should use the new ones.


###Tags
- Removed `/tags/{TAGNAME}/shouts` use `/shouts?tags={TAGNAME}` instead.

###Discover
- Removed `/discover/{DISCOVER_ID}/shouts` use `/shouts?discover={DISCOVER_ID}` instead.

###Shouts
- Removed `tags` property from **Shout** object and replaced it with `filters`.
- `filters` is a list of **Filter** objects.
- **Shout Filter** is an object used to describe the shouts in more details.
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
- `price` is now a big integer field and deals with cents!
- Added categories endpoint `/shouts/categories` which along with the categories it returns `filters` property. The only difference between **Shout Filter** and **Category Filter** is that category filters have `values` instead of `value`. This helps when creating or editing shouts, also when filtering the search by passing those as query parameters.

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
