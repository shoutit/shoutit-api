### Env variables

`SHOUTIT_ENV` should be set before starting the server. These (except `SHOUTIT_ENV`) should be set in an `.env` file located in `src/configs`.
The filename should match `SHOUTIT_ENV` value e.g if it is `local` the file should be `local.env`.

| Name                                          | Default       | Notes                                                          |
|-----------------------------------------------|---------------|----------------------------------------------------------------|
| `API_LINK`                                    |               |                                                                |
| `DB_HOST`,`DB_PORT`, `DB_USER`, `DB_PASSWORD` |               |                                                                |
| `EMAIL_ENV`                                   |               | Can be either `file` or `sendgrid`                             |
| `ES_HOST`, `ES_PORT`, `ES_BASE_INDEX`         |               |                                                                |
| `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`      |               |                                                                |
| `FORCE_SYNC_RQ`                               | `False`       | When true, RQ jobs will be executed on the same request thread |
| `MIXPANEL_TOKEN`                              |               |                                                                |
| `PUSHER_ENV`                                  | `SHOUTIT_ENV` value |                                                                |
| `RAVEN_DSN`                                   |               | whennot provided Sentry won't be used for logging errors       |
| `REDIS_HOST`,`REDIS_PORT`                     |               |                                                                |
| `SHOUTIT_DEBUG`                               |               | Any truth value                                                |
| `SHOUTIT_ENV`                                 |               | Should be one of the following: `prod`, `dev` or `local`       |
| `SITE_LINK`                                   |               |                                                                |
| `TWILIO_ENV`                                  | `SHOUTIT_ENV` value|                                                                |


Other loadbalancer related variables that can be used on Docker. They should be also set outside the .

- `FORCE_SSL`
- `VIRTUAL_HOST`
