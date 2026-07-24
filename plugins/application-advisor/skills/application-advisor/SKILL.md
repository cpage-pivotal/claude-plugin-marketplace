---
name: application-advisor
description: >
  Integrate Broadcom's Application Advisor (Tanzu Spring) to automate Spring
  dependency upgrades and security patches in a Git repository. Use this skill
  whenever the user wants to set up Application Advisor, automate Spring Boot
  upgrades, apply security/bug-fix patches to dependencies, run OpenRewrite
  upgrade recipes against a Spring project, configure the Broadcom enterprise
  Maven repository, install the advisor CLI, get an upgrade plan for a Spring
  app, create upgrade mappings for third-party libraries, configure
  `.advisor.yml`, or add a GitHub Actions workflow that opens upgrade or patch
  PRs automatically. Trigger even if the user only mentions "Spring upgrades",
  "App Advisor", "advisor CLI", "Broadcom registry token", "patch apply",
  "advisor.yml", or "automate dependency bumps" without naming the tool
  explicitly.
---

# Application Advisor Integration

[Application Advisor](https://techdocs.broadcom.com/us/en/vmware-tanzu/spring/application-advisor/1-6/app-advisor/what-is-app-advisor.html)
continuously and incrementally upgrades Spring dependencies in Git repositories
by computing upgrade plans with OpenRewrite recipes and opening PRs with the
changes applied.

This skill walks through the full integration from scratch. Work through the
steps in order, confirming with the user at each stage before proceeding. If
the user is resuming partway through (e.g., they already have a registry token
or the CLI is already installed), skip the completed steps.

---

## Step 1 — Generate a Broadcom Registry Token

The CLI and enterprise Maven artifacts require a registry token tied to a
Broadcom Support Portal account with a Spring Enterprise subscription.

Direct the user to:

1. Log in at **https://support.broadcom.com** with an Enterprise User profile
2. Navigate to **My Downloads → Registry Tokens**
3. Click **Generate Registry Token**
4. Copy the token — it will be needed throughout the rest of this setup

Reference: https://knowledge.broadcom.com/external/article/421110

Once the user has the token, ask for their **Broadcom account email address**
as well — both are needed for Maven credentials.

---

## Step 2 — Configure `~/.m2/settings.xml`

The enterprise Maven repo and the advisor CLI both authenticate using the
registry token. Add a `spring-enterprise-subscription` server entry to
`~/.m2/settings.xml`.

**Important gotcha:** The advisor CLI's `MavenSettingsReader` throws a
`NullPointerException` if any `<server>` entry in the file is missing a
`<password>` element — even servers unrelated to Application Advisor (e.g., a
GCP Artifact Registry server with only a `<configuration>` block). Add empty
`<username>` and `<password>` tags to any server that currently lacks them.

```xml
<settings>
  <servers>
    <!-- Add to any existing servers that lack username/password: -->
    <!-- <server>
      <id>existing-server-id</id>
      <username></username>
      <password></password>
      ... existing config ...
    </server> -->

    <server>
      <id>spring-enterprise-subscription</id>
      <username>YOUR_BROADCOM_EMAIL</username>
      <password>YOUR_REGISTRY_TOKEN</password>
    </server>
  </servers>
</settings>
```

Read the existing `~/.m2/settings.xml` before editing so you don't overwrite
other server entries. Create the file if it doesn't exist.

---

## Step 3 — Add the Enterprise Repository to `pom.xml`

Add the Broadcom enterprise Maven repository so the project can resolve
commercial Spring artifacts and upgrade recipes. The `<id>` must exactly match
the server id in `settings.xml`.

```xml
<repositories>
    <repository>
        <id>spring-enterprise-subscription</id>
        <url>https://packages.broadcom.com/artifactory/spring-enterprise</url>
    </repository>
</repositories>
<pluginRepositories>
    <pluginRepository>
        <id>spring-enterprise-subscription</id>
        <url>https://packages.broadcom.com/artifactory/spring-enterprise</url>
    </pluginRepository>
</pluginRepositories>
```

Place these blocks before `<build>` in `pom.xml`. For Gradle projects, see the
[artifact repository guide](https://techdocs.broadcom.com/us/en/vmware-tanzu/spring/tanzu-spring/commercial/spring-tanzu/guide-artifact-repository-developers.html).

---

## Step 4 — Install the Advisor CLI

**Prerequisite:** Java 17 minimum on `$PATH` to run the CLI itself (a JDK
manager like sdkman is handy if the target project builds with an older
Java version — e.g. 8 or 11 — since the CLI still needs 17+ to execute even
when patching/upgrading a project on an older baseline).

Detect the OS and CPU architecture (`uname -s` and `uname -m`) and download
the matching binary from the enterprise repo. Resolve the latest available
version dynamically at install time.

| OS | Architecture | Variant |
|----|-------------|---------|
| Linux | x86_64 | `linux` |
| macOS | Intel (x86_64) | `macos` |
| macOS | Apple Silicon (arm64) | `macos-arm64` |
| Windows | x86_64 | `windows` |

Base download URL pattern:
```
https://packages.broadcom.com/artifactory/spring-enterprise/com/vmware/tanzu/spring/
  application-advisor-cli-{VARIANT}/{VERSION}/application-advisor-cli-{VARIANT}-{VERSION}.tar
```

Resolve the latest version via the Artifactory API, then download:

**macOS ARM64 example:**
```bash
REGISTRY_TOKEN="<token>"

# Resolve latest released version
ADVISOR_VERSION=$(curl -sf \
  -H "Authorization: Bearer $REGISTRY_TOKEN" \
  "https://packages.broadcom.com/artifactory/api/search/latestVersion?g=com.vmware.tanzu.spring&a=application-advisor-cli-linux&repos=spring-enterprise")

curl -fsSL \
  -H "Authorization: Bearer $REGISTRY_TOKEN" \
  -o /tmp/advisor-cli.tar \
  "https://packages.broadcom.com/artifactory/spring-enterprise/com/vmware/tanzu/spring/application-advisor-cli-macos-arm64/${ADVISOR_VERSION}/application-advisor-cli-macos-arm64-${ADVISOR_VERSION}.tar"

mkdir -p ~/bin
tar -xf /tmp/advisor-cli.tar -C ~/bin --strip-components=1 --exclude=./META-INF
```

Verify with `~/bin/advisor --version`.

If `~/bin` is not on `$PATH`, remind the user to add `export PATH="$HOME/bin:$PATH"`
to their shell profile (`~/.zshrc` or `~/.bashrc`).

---

## Step 5 — Run the Advisor

From the project root directory:

```bash
# Analyse the project — generates target/.advisor/build-config.json
advisor build-config get

# Compute what can be upgraded
advisor upgrade-plan get
```

### Interpreting the upgrade plan output

**"No upgrade plans available — your project seems to be up to date"** with a
list of blocking dependencies means the project *does* have available upgrades,
but some direct dependencies are blocking them. This is the advisor's safety
mechanism: it won't upgrade a library (e.g., Spring Boot) if doing so would
leave another direct dependency (e.g., Spring AI) targeting an incompatible
older version.

**"Projects discovered: spring-ai-bom: 1.1.x → 2.0.x"** with a Step 1 at the
bottom means a concrete upgrade plan was found — run `advisor upgrade-plan apply`
to apply it.

### Handling blockers

When dependencies show up as blockers, there are two paths:

**Option A — Generate custom upgrade mappings** (for libraries you control or
that are available in Maven Central):
```bash
# Generates mapping files in .advisor/mappings/
advisor mapping create -c='org.springframework.ai:spring-ai-bom' --isBom

# Point the advisor at them when running
SPRING_ADVISOR_MAPPING_CUSTOM_0_FILEPATH=.advisor/mappings \
  advisor upgrade-plan get
```
This is best for internal shared libraries or any open-source library whose
upgrade history is fully available in Maven. It becomes burdensome to maintain
for large transitive dependency graphs (e.g., Spring AI + MCP SDK together).

**Option B — Upgrade blockers manually, then use the advisor for the rest.**
For example, if Spring AI is blocking a Spring Boot upgrade, bump `spring-ai.version`
in `pom.xml` by hand first, then re-run `advisor upgrade-plan get`. See the
[OpenRewrite recipes section](#openrewrite-recipes) below for automated
Spring Boot 4.x migration.

---

## Step 6 — Apply an Upgrade

When an upgrade plan is available:

```bash
# Apply the first upgrade step
advisor upgrade-plan apply

# With code formatting (if the project uses Spring Java Format)
advisor upgrade-plan apply --after-upgrade-cmd=spring-javaformat:apply
```

The `--squash=N` flag combines N upgrade steps into a single PR, which is useful
when you want to reduce PR noise.

> **Avoid `--push` for PR creation.** The advisor auto-generates branch names by
> concatenating every upgraded library (e.g.,
> `spring-boot-to-3.4.x-hibernate-orm-to-6.6.x-jackson-to-2.18.x-…`). Steps
> that upgrade many libraries produce branch names exceeding GitHub's 255-byte ref
> limit, causing PR creation to fail with a 422 error even though the upgrade was
> applied successfully. Use the GitHub Actions workflow approach in Step 8 instead,
> which creates a short datestamped branch name.

---

## Step 7 — Apply Security Patches

Since 1.6.5, the advisor can also **patch** dependencies instead of upgrading
them. A patch stays within the dependency's current minor version and picks up
CVE fixes and bug fixes (e.g. `2.7.3` → `2.7.34.1`), whereas `upgrade-plan`
moves to a new minor or major version. Use patches when the user wants CVEs
closed without the risk of a version bump; use `upgrade-plan` (Steps 5–6) when
they want to move onto a newer release line.

```bash
advisor patch apply
```

This queries the latest available patch version for every dependency in the
project's SBOM and rewrites `pom.xml` / `build.gradle` in place: explicit
dependency versions, the parent project version, managed dependency versions,
new managed dependencies where available, and removes redundant managed
libraries pulled in from imported SBOMs.

> Patch lookups hit Maven Central for every dependency in the SBOM, so
> `advisor patch apply` can take several minutes on a large project. It's
> designed to run regularly in CI, not interactively on every invocation.

### Automating patch PRs

Unlike `upgrade-plan apply` (see the `--push` warning in Step 6), patch PR
creation is safe to drive with `--push` directly — a patch step only ever
touches the version of one release line per dependency, so branch names don't
balloon the way concatenated upgrade branch names do:

```bash
advisor patch apply --push --from-yml
```

`--from-yml` reads settings from an `.advisor.yml` file in the repo root:

```yaml
enabled: true

ignore:
  # ignore a specific dependency entirely
  - dependency-name: "com.example:pinned-lib"
  # ignore only certain version ranges (Dependabot-style)
  - dependency-name: "org.springframework.boot"
    versions: ["3.x"]
  # wildcard an entire group
  - dependency-name: "com.acme:*"
```

`.advisor.yml` replaces the older `.spring-app-advisor.yml` filename — if both
are present, `.advisor.yml` takes precedence, though the old filename is still
recognized.

**Required for `--push`:** `GIT_TOKEN_FOR_PRS` with `repo` write access, same
as the upgrade workflow. Against a self-hosted Git instance, also pass
`--scm-host=<host>` or set the `ADVISOR_SCM_HOST` environment variable.

**Gradle projects resolving plugins from an internal repository** also need:
```bash
ADVISOR_DEFAULT_OSS_PLUGINS_REPOSITORY=<url>
ADVISOR_DEFAULT_OSS_PLUGINS_USERNAME=<user>
ADVISOR_DEFAULT_OSS_PLUGINS_PASSWORD=<password>
```

Reference: https://techdocs.broadcom.com/us/en/vmware-tanzu/spring/application-advisor/1-6/app-advisor/patch-spring-app.html

---

## Step 8 — GitHub Actions Workflow

Read `references/github-workflow.yml` for the complete upgrade-PR workflow
template, and `references/github-workflow-patch.yml` for the patch-PR
equivalent. The upgrade workflow runs on every push to `main`, downloads the
Linux advisor CLI, applies the upgrade with `advisor upgrade-plan apply`, then
opens a PR using a short datestamped branch name via the `gh` CLI. The patch
workflow instead runs on a schedule (patches are best applied regularly, not
on every push) and calls `advisor patch apply --push --from-yml`, which needs
an `.advisor.yml` with `enabled: true` committed to the repo. The two
workflows can coexist in the same repository.

**GitHub secrets to configure** (`Settings → Secrets → Actions`):

| Secret | Purpose |
|--------|---------|
| `BROADCOM_REGISTRY_TOKEN` | Registry token from Step 1 |
| `BROADCOM_USERNAME` | Broadcom account email |
| `GIT_TOKEN_FOR_PRS` | GitHub PAT with `repo` scope |

> Use a PAT (not `secrets.GITHUB_TOKEN`) for `GIT_TOKEN_FOR_PRS`. PRs created
> by the built-in `GITHUB_TOKEN` don't trigger other workflow runs, so CI checks
> on the upgrade/patch PR won't fire.

Write the workflow(s) to `.github/workflows/application-advisor.yml` and
`.github/workflows/application-advisor-patch.yml`.

---

## OpenRewrite Recipes

For cases where the advisor can't orchestrate an upgrade automatically (e.g.,
Spring AI is blocking a Spring Boot upgrade), Broadcom's commercial OpenRewrite
recipes can be run directly.

**Spring Boot 4.x** — Broadcom commercial recipes (latest: 1.7.1):

| Recipe ID | Target |
|-----------|--------|
| `com.vmware.tanzu.spring.recipes.boot40.UpgradeSpringBoot_4_0` | Spring Boot 4.0.x |
| `com.vmware.tanzu.spring.recipes.boot41.UpgradeSpringBoot_4_1` | Spring Boot 4.1.x |

Artifact: `com.vmware.tanzu.spring.recipes:spring-boot-4-upgrade-recipes:1.7.1`
(from the enterprise repo — requires the `spring-enterprise-subscription`
repository and credentials configured above)

Run via the Maven rewrite plugin:
```bash
./mvnw -B org.openrewrite.maven:rewrite-maven-plugin:6.22.1:runNoFork \
  -Drewrite.recipeArtifactCoordinates=com.vmware.tanzu.spring.recipes:spring-boot-4-upgrade-recipes:1.7.1 \
  -Drewrite.activeRecipes=com.vmware.tanzu.spring.recipes.boot41.UpgradeSpringBoot_4_1
```

**Spring AI 2.x** — No dedicated OpenRewrite recipe exists as of June 2026.
Bump the BOM version manually in `pom.xml`:
```xml
<spring-ai.version>2.0.0</spring-ai.version>
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `NullPointerException` in `MavenSettingsReader` on startup | A `<server>` in `settings.xml` has no `<password>` element | Add `<username></username><password></password>` to that server entry |
| HTTP 401 downloading CLI or resolving Maven artifacts | Expired or invalid registry token | Regenerate at https://support.broadcom.com |
| `advisor: command not found` | `~/bin` not on `$PATH` | Add `export PATH="$HOME/bin:$PATH"` to `~/.zshrc` or `~/.bashrc` |
| "No upgrade plans available" with a list of blockers | Third-party dependencies lack upgrade mappings | Use Option A or Option B from Step 5 above |
| `Could not apply the recipe(s)` with a `.advisor/errors/*.log` | An existing `rewrite-maven-plugin` in `pom.xml` has `<activeRecipes>` configured — Maven merges those recipes with the advisor's own, causing a conflict | Remove the `rewrite-maven-plugin` block from `pom.xml`; the advisor manages its own rewrite invocations |
| Upgrade PR doesn't trigger CI checks | `GIT_TOKEN_FOR_PRS` is `GITHUB_TOKEN` | Switch to a personal access token with `repo` scope |
| PR creation fails with `422 refs longer than 255 bytes are not allowed` | `advisor upgrade-plan apply --push` auto-generates a branch name listing every upgraded library; on steps with many libraries the name exceeds GitHub's limit | Don't use `--push`; instead run `advisor upgrade-plan apply` then open the PR with `gh pr create` using a short datestamped branch name (see `references/github-workflow.yml`) |
| `advisor patch apply` runs for several minutes with no output | Expected — it looks up the latest patch version for every SBOM dependency against Maven Central | Run it in CI on a schedule rather than interactively; not a hang |
| `advisor patch apply --from-yml` doesn't pick up ignore rules | Settings are in `.spring-app-advisor.yml` but `.advisor.yml` also exists | `.advisor.yml` takes precedence when both are present — consolidate settings there |
