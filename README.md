### Env variables

`SHOUTIT_ENV` should be set before starting the server. These (except `SHOUTIT_ENV`) should be set in an `.env` file located in `config/`.
The filename should match `SHOUTIT_ENV` value e.g if it is `live` the file should be `live.env`.

| Name                                          | Default       | Notes                                                          |
|-----------------------------------------------|---------------|----------------------------------------------------------------|
| `API_LINK`                                    |               |                                                                |
| `APP_LINK_SCHEMA`                             | `shoutit`     |                                                                |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`  |               |                                                                |
| `DB_HOST`,`DB_PORT`, `DB_USER`, `DB_PASSWORD` |               |                                                                |
| `EMAIL_ENV`                                   |               | Can be either `file` or `sendgrid`                             |
| `ES_HOST`, `ES_PORT`, `ES_BASE_INDEX`         |               |                                                                |
| `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`      |               |                                                                |
| `FORCE_SYNC_RQ`                               | `False`       | When true, RQ jobs will be executed on the same request thread |
| `MIXPANEL_TOKEN`                              |               |                                                                |
| `MIXPANEL_SECRET`                             |               |                                                                |
| `PUSHER_ENV`                                  | `SHOUTIT_ENV` value |                                                          |
| `RAVEN_DSN`                                   |               | whennot provided Sentry won't be used for logging errors       |
| `REDIS_HOST`,`REDIS_PORT`                     |               |                                                                |
| `SHOUTIT_DEBUG`                               |               | Any truth value                                                |
| `SHOUTIT_ENV`                                 |               | Should be one of the following: `live`, `stage`, `testing` or `development` |
| `SITE_LINK`                                   |               |                                                                |
| `TWILIO_ENV`                                  | `SHOUTIT_ENV` value|                                                           |


Other loadbalancer related variables that can be used on Docker. They should be also set outside the .

- `FORCE_SSL`
- `VIRTUAL_HOST`
