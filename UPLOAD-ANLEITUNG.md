# Publish to the Unraid Apps catalog

This is a local setup guide. Uploading it to the fork is optional.

## Upload the files to the existing fork

Repository: https://github.com/BomberPilot1/HoYo_Code_Sender_Discord_Bot

Extract the ZIP file. Under Add file > Upload files, drag the following files and folders into the root of the fork, preserving their directory structure:

```text
ca_profile.xml
UNRAID-APP.md
icons/hoyo-bot-character.png
templates/hoyo-bot.xml
```

Upload the extracted contents, keeping the paths shown above. Uploading the ZIP itself or its enclosing download folder would make the raw file URLs incorrect.
Choose Commit changes to save the files on main. Keep the existing LICENSE, Dockerfile and workflows.

## Enable support

In the fork, enable Settings > General > Features > Issues if it is not already enabled. The template links to this fork's Issues page for support.

## Check before submitting

- Confirm that the Docker package `ghcr.io/bomberpilot1/hoyo-bot:latest` is public and the build succeeds.
- Confirm that the repository is public and its existing open-source license remains in the root directory.
- After uploading, confirm that these raw URLs serve the files:
  - https://raw.githubusercontent.com/BomberPilot1/HoYo_Code_Sender_Discord_Bot/main/ca_profile.xml
  - https://raw.githubusercontent.com/BomberPilot1/HoYo_Code_Sender_Discord_Bot/main/templates/hoyo-bot.xml
  - https://raw.githubusercontent.com/BomberPilot1/HoYo_Code_Sender_Discord_Bot/main/icons/hoyo-bot-character.png
- Confirm that the public template contains no real tokens, passwords, user IDs, host IP addresses or personal network names.
- Test a fresh installation from the new template: input fields, livestream tracking switch, optional YouTube API key, network selection, MongoDB connection and /setup.
- The template maps host port 3000 to container port 3000 by default. If the existing container already uses that host port, select a different host port for the test. The WebUI link opens the bot's built-in web server rather than the separate Next.js dashboard.

The existing container already works. A fresh installation must still be checked to verify the new public XML template.

## Test the new template on Unraid

After uploading the files to GitHub, run this command in the Unraid terminal:

```bash
curl -fL "https://raw.githubusercontent.com/BomberPilot1/HoYo_Code_Sender_Discord_Bot/main/templates/hoyo-bot.xml" -o /boot/config/plugins/dockerMan/templates-user/my-HoYo-Code-Sender-CA-Test.xml
```

Then open Docker > Add Container and select the new template from the template dropdown.
Stop the existing bot before starting the test container. The existing MongoDB container can keep running.
For the test container, choose the same custom network as MongoDB and enter the existing credentials again.
Start the test container and check its logs and /listcodes. Afterwards, you may stop the test container and restart the original container.

## Submit

1. Open https://ca.unraid.net/submit and choose Start Submission.
2. Sign in with your own Unraid account.
3. Enter the repository URL: https://github.com/BomberPilot1/HoYo_Code_Sender_Discord_Bot.
4. Run Validate, then Scan. Resolve any reported issues.
5. Review the preview and submit for review.

Once approved, the app appears in a subsequent catalog build. Approval and processing times are not guaranteed.
As the maintainer, you handle support for this template and your image. Keep the attribution to the original author, chiraitori.

## Verification status of this package

The XML files were checked locally for syntax, required fields, consistent URLs and empty credential fields. The new PNG icon was edited from the supplied screenshot using ImageGen.
Uploading these files to GitHub, testing an installation from this new XML file and validating the package in the Community Apps portal have not been performed here.

## Official sources

- https://ca.unraid.net/submit/help/repository-xml
- https://ca.unraid.net/submit/help/repository-info-xml
- https://ca.unraid.net/submit/help/xml-field-reference
- https://ca.unraid.net/submit/help/builders
