import sys
from functools import partial

from click import option, group, argument

from git_id.profile import ProfileManager, GitManager


print_err = partial(print, file=sys.stderr)


@group(no_args_is_help=True)
def git_id():
    ...


@git_id.command(help="info about the current identity for the git repository you're in")
def info():
    git = GitManager()
    local_profile = git.get_profile()
    if not local_profile:
        print_err("Couldn't retrieve profile information")
        return sys.exit(1)
    manager = ProfileManager()
    matching_profile = [profile for profile in manager.list_profiles() if profile == local_profile][:1]
    if matching_profile:
        profile = matching_profile[0]
        print(f"{profile.id} - {profile}")
        return sys.exit(0)
    else:
        profile = local_profile
        print(f"{profile}")
        print("\nThis profile is not registered yet.")
        register_choice = input("register? (y/N):") in "yY"
        if not register_choice:
            return sys.exit(0)
        profile.id = input(f"Set an id to the profile ({profile.id}):") or profile.id
        manager.save_profile(profile)
        manager.save()
        return sys.exit(0)


@git_id.command(help="list registered identities")
def ls():
    manager = ProfileManager()
    profiles = manager.list_profiles()
    if not profiles:
        print_err("No profiles available")
    local_profile = GitManager().get_profile()
    for profile in profiles:
        print(
            f"{'*' if profile == local_profile else ' '} "
            f"{profile.id} - {profile}"
        )


@git_id.command(help="use [profile_id] for current git repository")
@argument("profile_id")
def use(profile_id: str):
    manager = ProfileManager()
    profile = manager.get_profile(profile_id)
    if not profile:
        print_err(f"Profile '{profile_id}' not found.")
        return sys.exit(2)
    git = GitManager()
    if not git.repo:
        print_err(f"Couldn't retrieve information about current repo")
        return sys.exit(1)
    git.save_profile(profile)
    print(f"Current Identity: {profile}")


@git_id.command(help="create new identity")
@option("--profile_id", default=None)
@option("--name", default=None)
@option("--email", default=None)
@option("--gpg_key", default=None)
def create(
        profile_id: str = None,
        name: str = None,
        email: str = None,
        gpg_key: str = None
):
    manager = ProfileManager()
    profile = manager.create(name, email, gpg_key, profile_id)
    if not profile:
        print_err("Cancelled.")
        return sys.exit(0)
    manager.save_profile(profile)
    manager.save()
    print_err(f"Saved Identity: {profile.id} - {profile}")


def main():
    git_id(prog_name="git id")
