# shoutit-api v3 changelog



## Initial commits (2016-02-22)

- Live documentation: http://dev.api.shoutit.com/docs/
- V3 base url: http://dev.api.shoutit.com/v3/

### OAuth2

- Changed `shoutit_signin` to `shoutit_login`
- Added `shoutit_guest` grant type to OAuth2 endpoint (notice the returned `GuestUser` object)