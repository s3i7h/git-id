# git-id
An ID manager for git.

An Identity / Profile consists of name, email, and signingkey, and this command aims to manage them and help switch between them seamlessly.

# how to install

```
$ pip install git-id
```

# Usage

## `info` - show info / add identity
```
$ git id info
```

`info` will retrieve identity from current repository and search a matching identity in the registry (`$HOME/.git-id.yml`).

If no matching identity is found, then asks you if you want to register it.

## `list` - list identities in the registry
```
$ git id list
```

`list` will show all the identities in the registry.

## `use` - use an identity
```
$ git id use <profile_id>
```

`use` will set the identity of the current repository to the identity `<profile_id>` in the registry.

## `create` - create an identity
```
$ git id create
```

`create` will create + register a new identity interactively/non-interactively.
