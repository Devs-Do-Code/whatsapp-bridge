# Contributing to whatsapp-bridge

First off, thank you for considering contributing to whatsapp-bridge! It's people like you that make this project great.

## Where do I go from here?

If you've noticed a bug or have a feature request, [make one](https://github.com/Devs-Do-Code/whatsapp-bridge/issues/new)! It's generally best if you get confirmation of your bug or approval for your feature request this way before starting to code.

If you have a general question, feel free to ask in the [Discussions section](https://github.com/Devs-Do-Code/whatsapp-bridge/discussions).

## Fork & create a branch

If this is something you think you can fix, then fork whatsapp-bridge and create a branch with a descriptive name.

A good branch name would be (where issue #123 is the ticket you're working on):

```bash
git checkout -b 123-fix-bug-description
```

## Get the code

```bash
git clone https://github.com/<your-username>/whatsapp-bridge.git
cd whatsapp-bridge
git checkout 123-fix-bug-description
```

## Implement your fix or feature

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first :smile_cat:

## Make a Pull Request

At this point, you should switch back to your master branch and make sure it's up to date with whatsapp-bridge's master branch:

```bash
git remote add upstream https://github.com/Devs-Do-Code/whatsapp-bridge.git
git checkout master
git pull upstream master
```

Then update your feature branch from your local copy of master, and push it!

```bash
git checkout 123-fix-bug-description
git rebase master
git push --set-upstream origin 123-fix-bug-description
```

Finally, go to GitHub and make a Pull Request :D

## Keeping your Pull Request updated

If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.

To learn more about rebasing, check out [this guide](https://docs.github.com/en/get-started/using-git/about-git-rebase).

## Code Style

Please follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. Use linters like Flake8 or Pylint to check your code.

## Commit Messages

Please follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for commit messages. This helps in automating changelog generation and understanding the history.

Example:
```
feat: add support for sending stickers
fix: resolve issue with message delivery status
docs: update README with installation instructions
```

Thank you for contributing!
