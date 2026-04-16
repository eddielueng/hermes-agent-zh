1s

Current runner version: '2.333.1'

Runner Image Provisioner

Operating System

Runner Image

GITHUB\_TOKEN Permissions

Secret source: Actions

Prepare workflow directory

Prepare all required actions

Getting action download info

Download action repository 'actions/checkout\@v4' (SHA:34e114876b0b11c390a56381ad16ebd13914f8d5)

Download action repository 'actions/setup-python\@v5' (SHA:a26af69be951a213d495a4c3e4e4022e16d87065)

Download action repository 'actions/upload-artifact\@v4' (SHA:ea165f8d65b6e75b540449e92b4886f43607fa02)

Complete job name: Sync & Translate

3s

Run actions/checkout\@v4

Syncing repository: eddielueng/hermes-agent-zh

Getting Git version info

Temporarily overriding HOME='/home/runner/work/\_temp/4cec4676-fa9a-487b-9c87-8636e8730488' before making global git config changes

Adding repository directory to the temporary git global config as a safe directory

/usr/bin/git config --global --add safe.directory /home/runner/work/hermes-agent-zh/hermes-agent-zh

Deleting the contents of '/home/runner/work/hermes-agent-zh/hermes-agent-zh'

Initializing the repository

Disabling automatic garbage collection

Setting up auth

Fetching the repository

Determining the checkout info

/usr/bin/git sparse-checkout disable

/usr/bin/git config --local --unset-all extensions.worktreeConfig

Checking out the ref

/usr/bin/git log -1 --format=%H

86f2744d050101f2dfb099460a7422a1d2a13ea7

0s

Run git config --global user.name "Hermes Bot"

\=== Current repo info ===

origin	<https://github.com/eddielueng/hermes-agent-zh> (fetch)

origin	<https://github.com/eddielueng/hermes-agent-zh> (push)

Current branch: main

Current HEAD: 86f2744d050101f2dfb099460a7422a1d2a13ea7

0s

Run echo "=== Step 1: Add upstream remote ==="

\=== Step 1: Add upstream remote ===

Remotes configured:

origin	<https://github.com/eddielueng/hermes-agent-zh> (fetch)

origin	<https://github.com/eddielueng/hermes-agent-zh> (push)

upstream	<https://github.com/nousresearch/hermes-agent.git> (fetch)

upstream	<https://github.com/nousresearch/hermes-agent.git> (push)

\=== Step 2: Fetch upstream main ===

From <https://github.com/nousresearch/hermes-agent>

&#x20;\* branch              main       -> FETCH\_HEAD

&#x20;\* \[new branch]        main       -> upstream/main

Fetch exit code: 0

\=== Step 3: Get commit SHAs ===

Local HEAD:  86f2744d050101f2dfb099460a7422a1d2a13ea7

Remote HEAD: 206259d1118bace16a53a40f06dc5466c94ff737

Remote exit code: 0

\=== Step 4: Check differences ===

Commits ahead: 33

✅ Found 33 commits to sync

1s

Run BRANCH\_NAME="auto-sync-$(date +%Y%m%d-%H%M%S)"

Switched to a new branch 'auto-sync-20260414-165357'

Auto-merging README.md

CONFLICT (content): Merge conflict in README.md

Auto-merging hermes\_cli/commands.py

Auto-merging hermes\_cli/main.py

CONFLICT (content): Merge conflict in hermes\_cli/main.py

Auto-merging hermes\_cli/setup.py

Auto-merging hermes\_cli/status.py

Auto-merging tools/skills\_tool.py

Automatic merge failed; fix conflicts and then commit the result.

⚠️ Merge had conflicts or warnings, continuing...

✅ Merge complete

Files changed:

.github/workflows/auto-translate.yml

AGENTS.md

README.md

agent/anthropic\_adapter.py

agent/prompt\_builder.py

cli-config.yaml.example

cli.py

cron/scheduler.py

docs/skins/example-skin.yaml

gateway/config.py

gateway/platforms/\_\_init\_\_.py

gateway/platforms/matrix.py

gateway/platforms/qqbot.py

gateway/platforms/telegram.py

gateway/platforms/webhook.py

gateway/run.py

gateway/stream\_consumer.py

hermes\_cli/commands.py

hermes\_cli/config.py

hermes\_cli/dump.py

hermes\_cli/gateway.py

hermes\_cli/main.py

hermes\_cli/model\_switch.py

hermes\_cli/models.py

hermes\_cli/platforms.py

hermes\_cli/plugins.py

hermes\_cli/runtime\_provider.py

hermes\_cli/setup.py

hermes\_cli/skin\_engine.py

hermes\_cli/status.py

0s

Run actions/setup-python\@v5

Installed versions

1s

Run pip install pyyaml

Collecting pyyaml

&#x20; Downloading pyyaml-6.0.3-cp311-cp311-manylinux2014\_x86\_64.manylinux\_2\_17\_x86\_64.manylinux\_2\_28\_x86\_64.whl.metadata (2.4 kB)

Downloading pyyaml-6.0.3-cp311-cp311-manylinux2014\_x86\_64.manylinux\_2\_17\_x86\_64.manylinux\_2\_28\_x86\_64.whl (806 kB)

&#x20;  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 806.6/806.6 kB 74.5 MB/s  0:00:00

Installing collected packages: pyyaml

Successfully installed pyyaml-6.0.3

3s

1s

Run git add -A

\[auto-sync-20260414-165357 7ce8bb57] Auto translate: 4 files translated to Chinese

remote:

remote: Create a pull request for 'auto-sync-20260414-165357' on GitHub by visiting:

remote:      <https://github.com/eddielueng/hermes-agent-zh/pull/new/auto-sync-20260414-165357>

remote:

To <https://github.com/eddielueng/hermes-agent-zh>

&#x20;\* \[new branch]        auto-sync-20260414-165357 -> auto-sync-20260414-165357

✅ Done!

1s

Run echo "Current branch: $(git branch --show-current)"

Current branch: auto-sync-20260414-165357

Creating PR from branch: auto-sync-20260414-165357

could not add label: 'automated' not found

PR creation failed, trying without labels...

pull request create failed: GraphQL: Head sha can't be blank, Base sha can't be blank, No commits between main and auto-sync-20260414-165357, Head ref must be a branch (createPullRequest)

PR may already exist

Branch URL: <https://github.com/eddielueng/hermes-agent-zh/tree/auto-sync-20260414-165357>

1s

Run actions/upload-artifact\@v4

(node:2483) \[DEP0040] DeprecationWarning: The \`punycode\` module is deprecated. Please use a userland alternative instead.

(Use \`node --trace-deprecation ...\` to show where the warning was created)

With the provided path, there will be 2 files uploaded

Artifact name is valid!

Root directory input is valid!

Beginning upload of artifact content to blob storage

(node:2483) \[DEP0169] DeprecationWarning: \`url.parse()\` behavior is not standardized and prone to errors that have security implications. Use the WHATWG URL API instead. CVEs are not issued for \`url.parse()\` vulnerabilities.

Uploaded bytes 18488

Finished uploading artifact content to blob storage!

SHA256 digest of uploaded artifact zip is b51b38e4f129d9bafd56e68b5befdf2aeb75a8917792c979d38371ec13c9d51f

Finalizing artifact upload

Artifact translation-report-24411876833.zip successfully finalized. Artifact ID 6433280836

Artifact translation-report-24411876833 has been successfully uploaded! Final size is 18488 bytes. Artifact ID is 6433280836

Artifact download URL: <https://github.com/eddielueng/hermes-agent-zh/actions/runs/24411876833/artifacts/6433280836>

0s

Post job cleanup.

(node:2495) \[DEP0040] DeprecationWarning: The \`punycode\` module is deprecated. Please use a userland alternative instead.

(Use \`node --trace-deprecation ...\` to show where the warning was created)

0s

Post job cleanup.

/usr/bin/git version

git version 2.53.0

Copying '/home/runner/.gitconfig' to '/home/runner/work/\_temp/2375c608-f03b-4f5e-a8b8-615bdb49e2e3/.gitconfig'

Temporarily overriding HOME='/home/runner/work/\_temp/2375c608-f03b-4f5e-a8b8-615bdb49e2e3' before making global git config changes

Adding repository directory to the temporary git global config as a safe directory

/usr/bin/git config --global --add safe.directory /home/runner/work/hermes-agent-zh/hermes-agent-zh

/usr/bin/git config --local --name-only --get-regexp core\\.sshCommand

/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"

/usr/bin/git config --local --name-only --get-regexp http\\.https\\:\\/\\/github\\.com\\/\\.extraheader

http.<https://github.com/.extraheader>

/usr/bin/git config --local --unset-all http.<https://github.com/.extraheader>

/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\\.https\\:\\/\\/github\\.com\\/\\.extraheader' && git config --local --unset-all 'http.<https://github.com/.extraheader>' || :"

/usr/bin/git config --local --name-only --get-regexp ^includeIf\\.gitdir:

/usr/bin/git submodule foreach --recursive git config --local --show-origin --name-only --get-regexp remote.origin.url

0s

Cleaning up orphan processes

**Warning:** Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout\@v4, actions/setup-python\@v5, actions/upload-artifact\@v4. For more information see: <https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/>

<br />

<br />

<br />

<br />

0s

Current runner version: '2.333.1'

Runner Image Provisioner

Operating System

Runner Image

GITHUB\_TOKEN Permissions

Secret source: Actions

Prepare workflow directory

Prepare all required actions

Complete job name: Summary

0s

Run echo "## Auto Translation Report" >> $GITHUB\_STEP\_SUMMARY

1s

Cleaning up orphan processes
