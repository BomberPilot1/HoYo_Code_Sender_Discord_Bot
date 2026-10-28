# HoYo Code Sender on Unraid

Automatically post redemption codes for Genshin Impact, Honkai: Star Rail, and Zenless Zone Zero in Discord.

The original bot is developed by [chiraitori](https://github.com/chiraitori/HoYo_Code_Sender_Discord_Bot). This fork, Docker image and Unraid template are maintained by [BomberPilot1](https://github.com/BomberPilot1). This is an independent fan project, not affiliated with HoYoverse.

## Requirements

- An Intel/AMD Unraid server (`linux/amd64`).
- Your own Discord bot application, bot token and application ID from the [Discord Developer Portal](https://discord.com/developers/applications).
- A reachable MongoDB database, either a separate container or an external service such as MongoDB Atlas.

## Installation

1. Install MongoDB first, or prepare the connection string for an existing MongoDB database. MongoDB is installed separately from this bot.
2. Install this template in Unraid. The image is `ghcr.io/bomberpilot1/hoyo-bot:latest`.
3. If MongoDB runs in a local container, select the same user-defined Docker network for both containers. The default `bridge` setting in the public template is generic; change it to your own user-defined network before starting if using container-name resolution.
4. Fill in the required variables listed below. Do not share your bot token or database credentials in issues, screenshots, commits or public templates.
5. Invite your Discord application to your server with the `bot` and `applications.commands` scopes. Grant the bot the channel permissions it needs to view the target channel, send messages, embed links and read message history. Grant thread permissions if using thread delivery.
6. Start MongoDB, then the bot. In the bot logs, check for `Connected to MongoDB` and `Logged in as ...`.
7. In Discord use `/setup` to choose the channel and roles, `/favgames` to select games, and `/toggleautosend` to enable automatic notifications. `/listcodes` can be used to check code retrieval.

## Configuration

| Variable | Required | Description |
|---|---|---|
| `DISCORD_TOKEN` | Yes | Token for your own Discord bot. |
| `CLIENT_ID` | Yes | Application ID of the same Discord application. |
| `MONGODB_URI` | Yes | MongoDB connection string including database name and authentication. |
| `OWNER_ID` | No | Your Discord user ID for owner-specific commands. |
| `LIVESTREAM_TRACKING_ENABLED` | No | `true` by default. Choose `false` to disable livestream and HoYoLAB post tracking. |
| `YOUTUBE_API_KEY` | No | Your YouTube Data API key for improved YouTube live/upcoming status and schedule detection. |

The template also maps TCP host port `3000` to container port `3000` for the bot's built-in web/API server. If host port `3000` is already used, change the host-side value while keeping container port `3000`.

Discord tokens, MongoDB connection strings and YouTube API keys are masked in the template's input fields and have no personal values prefilled. Each user enters their own credentials during installation.

Example connection string for MongoDB on the same user-defined Docker network:

```text
mongodb://USER:PASSWORD@mongodb:27017/hoyo?authSource=admin
```

Replace `USER`, `PASSWORD`, and `mongodb` with your actual database username, URL-encoded password and MongoDB container name. This example authenticates against `admin`, suitable for a user created with the official MongoDB image's `MONGO_INITDB_ROOT_USERNAME` and `MONGO_INITDB_ROOT_PASSWORD` settings. For other MongoDB users, use the authentication database where that user was created.

The internal MongoDB port is `27017`. A host-side mapped port is not used when connecting directly by container name.

For external MongoDB deployments, use their provided connection string, configure their access controls for your Unraid server, and follow the provider's TLS settings.

## Storage and web access

Bot configuration and notification history are stored in MongoDB. Back up your database and keep its data on persistent storage.

The template does not require a local appdata mapping for the bot. It starts the Discord bot process and publishes its built-in web/API server on host port `3000` by default. The Unraid WebUI menu entry opens that server. The Discord bot itself does not require an incoming port; remove the port mapping if you do not need web/API access. The separate Next.js dashboard from the original project is not started by this image.

Warnings about missing optional `TOPGG_TOKEN`, `WEBHOOK_PASSWORD`, or `VERSION` do not by themselves prevent the bot from starting. Do not use the original developer's credentials.

## Updates

The fork's GitHub Actions workflow periodically checks for upstream changes and publishes successful builds to GitHub Container Registry. To use a new image, update the container in Unraid. Publishing a new image alone does not replace an already running container.

When moving an existing bot from another host, stop its previous instance before starting the same bot identity here.

## Support

For problems with this image or Unraid template, open an issue in [this fork's issue tracker](https://github.com/BomberPilot1/HoYo_Code_Sender_Discord_Bot/issues). Include your Unraid version and relevant logs with tokens, passwords and other private values removed.

Original project: [chiraitori/HoYo_Code_Sender_Discord_Bot](https://github.com/chiraitori/HoYo_Code_Sender_Discord_Bot).

## License

The bot remains under the project's existing [GPL license](LICENSE). Keep the original license and attribution. This fork's Unraid template, metadata and documentation use the same repository license.

The character icon is adapted from a user-provided game screenshot. The depicted game character and original artwork belong to their respective rights holders.
