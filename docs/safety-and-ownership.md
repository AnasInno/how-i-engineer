# Safety and Ownership

## Main Branch

Read actions may run on `main`. Mutating lane actions are refused. Starting a
normal task from clean primary `main` creates a linked worktree automatically.

## Owned State

Every mutable resource is tied to the current worktree lane:

- runtime directory;
- database;
- ports;
- app, worker and gateway processes;
- browser profile;
- logs and evidence;
- tester lock when explicitly acquired.

Cleanup stops only recorded owned processes and removes only verified descendants
of the ignored lane directory. Shared tester ownership is released explicitly;
generic cleanup cannot silently release it.

## Destructive Command Guard

Recursive deletion is rejected when the target is empty, unresolved,
variable-expanded or resolves to a protected location. Protected targets include
the repository, worktree root, `.git`, filesystem root, user root and home
directory.

Ownership failure is a safe stop. The harness leaves uncertain state in place
and reports it rather than guessing.

## Secrets

Credentials are hydrated into lane-owned child process environments from
trusted ignored sources. They are not copied into:

- checked-in OMP config;
- prompts;
- lane metadata;
- logs;
- evidence;
- commits.

Lane-specific URLs, databases and sessions override live values. A local proof
request never grants production authority.

## External Boundaries

Tester use, external providers and live proof require explicit task authority.
The harness does not convert a general development request into permission for
production systems, teacher conversations, billing, DNS or deployments.
