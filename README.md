[![py-Discord.png](https://github.com/borisdayma/dalle-mini/raw/main/img/logo.png)](https://postimg.cc/TpGJwp0j)

[DALL·E Mini][]
===================
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg?style=flat-square)](https://www.python.org/downloads/)


[md-pypi]: https://pypi.org/project/Markdown/
[pyversion-button]: https://img.shields.io/pypi/pyversions/Markdown.svg

DALL·E mini as a discord bot. Use `!help` to see the commands.

- You can deploy the bot to heroku as a starting point.
- Fill out `data.yaml` and configure the bot.

[DALL·E Mini]: https://github.com/borisdayma/dalle-mini
[Sentry's]: https://sentry.io/

[Markdown]: https://daringfireball.net/projects/markdown/
[Features]: https://Python-Markdown.github.io#Features
[Available Extensions]: https://Python-Markdown.github.io/extensions

Docker installation
-------------

Add your bot token to the docker-compose.yml file (this will override the bot token in data.yaml), then build and run with docker-compose:

```
docker-compose build
docker-compose up -d
```

How do I request?
-------------

Pretty simple. Just type in:
```text
!dalle <query> 
e.g: !dalle Cats just won the super bowl
```
That's it! There's an option in the `data.yaml` config file to change the prefix if you so desire. If you do so, the above command's `!` will change to exactly whatever you set in the `bot_prefix` line.

Example (thanks to @Cosmin96 for the collage):

[![py-Discord.png](Assets/img.png)](https://postimg.cc/TpGJwp0j)

Can I use emotes in the prefix?
--------
Yes you can! To put an emote in the `bot_prefix` line:

1. Pull up your Discord client.
2. Type a backslash and then the emote that you want to use. (i.e. `\:haha:`)
3. Hit Return. The emote's ID should be sent as a message.
4. Copy that ID (in its entirety, do not drop the <> tags).
5. Paste it into the `bot_prefix` line in your `data.yaml` config file.
6. All done! You should be able to type your emote then your query.


Support
----
You may report bugs, ask for help, and discuss various other issues on the issues page.
Discord: Rawa.#7438

Change Log
----------
Version 1.0.1:
  - Images are sent in a collage.
  - Cleanup for collage added.

Version 1.0.0:
  - Initial release.
