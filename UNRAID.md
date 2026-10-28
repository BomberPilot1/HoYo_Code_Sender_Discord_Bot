# Run the Unraid bot from your own fork

Fork: https://github.com/BomberPilot1/HoYo_Code_Sender_Discord_Bot

Image: `ghcr.io/bomberpilot1/hoyo-bot:latest`

## Add the files

Upload these files to the fork using exactly these paths:

```text
Dockerfile.unraid
Dockerfile.unraid.dockerignore
.github/scripts/hoyo_sync_upstream.py
.github/workflows/hoyo-unraid.yml
UNRAID.md
```

Save all changes on `main`. Keep the existing `Dockerfile`, original README and license.
Extract the ZIP file and upload the individual files and folders to GitHub.
Under Actions, enable the `HoYo Fork - Sync and Docker` workflow for this setup. Leave unnecessary inherited deployment workflows disabled.

## Grant the fork access to the existing image

The `hoyo-bot` package was previously published from another repository.
Before the first build, open Packages > hoyo-bot > Package settings > Manage Actions access in your GitHub profile.
Choose Add repository, add the fork `BomberPilot1/HoYo_Code_Sender_Discord_Bot`, and grant it the Write role.
Keep the existing image publicly accessible.

This grants access to the container package. Discord and MongoDB credentials remain exclusively in Unraid.

## Start the workflow and switch over

1. Under Actions, open `HoYo Fork - Sync and Docker` and choose Run workflow if necessary.
2. Both jobs must succeed: `Update bot code in the fork` and `Build the image from the saved fork`.
3. If the sync job fails because write access is unavailable, check the repository or organization policies under Settings > Actions > General. The workflow requests `contents: write` only for the sync job.
4. In Unraid, keep the image source set to `ghcr.io/bomberpilot1/hoyo-bot:latest`. After the first successful fork build, update the image through Unraid and check the bot logs.
5. Then disable the old `HoYo Bot Docker Image` workflow in the previous standalone build repository. Otherwise, two independent workflows may publish to the same latest tag.
6. You may keep the old repository as a fallback.

A GitHub workflow publishes the image. Updating a running Unraid container still requires an update through Unraid or an automatic update mechanism configured there separately.

## How it works

- The workflow checks the original repository's `main` branch approximately every six hours. Pushes to your own `main` branch and Run workflow also start it.
- Upstream code changes are saved as a merge in your fork. The workflow does not force-push or reset your changes.
- Files under `.github/workflows/` retain the versions stored in your fork during automatic synchronization. Upstream code and history are merged, while upstream CI and deployment workflow changes are not activated automatically. No personal GitHub token is required.
- If conflicts occur outside the workflow files, the process stops before publishing an image. Resolve the conflict in your fork and run the workflow again.
- If the original repository is unavailable, a warning is shown and the image is built from the code already saved in your fork.
- Building and publishing still require access to GitHub, the container registry and npm package sources. A fork does not make these services available offline.
- New images receive the `latest` tag and a `sha-...` tag identifying the fork commit. Rebuilding the same code may include base-image or dependency updates, so the SHA tag is not an immutable digest.
- GitHub may delay scheduled runs. In public repositories, scheduled workflows are disabled after 60 days without repository activity; re-enable them under Actions when needed.
- The image targets Intel/AMD Unraid (`linux/amd64`) and starts the Discord bot. It does not start the separate web dashboard.

## Sources

- https://docs.github.com/en/pull-requests/how-tos/work-with-forks/syncing-a-fork
- https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow
- https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
