# Application Advisor

Automate Spring dependency upgrades in Git repositories using
[Broadcom Application Advisor](https://techdocs.broadcom.com/us/en/vmware-tanzu/spring/application-advisor/1-6/app-advisor/what-is-app-advisor.html).
Application Advisor analyses your project's dependency tree, computes upgrade
plans using OpenRewrite recipes, and opens pull requests with the changes
applied — continuously and incrementally.

This plugin gives Claude Code the knowledge to guide you through the full
integration: from obtaining a Broadcom registry token, through configuring
Maven credentials and installing the CLI, to running upgrade plans and wiring
everything into a GitHub Actions workflow that opens upgrade PRs automatically
on every push to `main`.

## Skills in this plugin

- **`application-advisor`** — end-to-end setup guide. Claude activates it
  automatically when you ask about Spring upgrades, Application Advisor, the
  advisor CLI, Broadcom registry tokens, or automated dependency management for
  Spring projects.

## What the skill covers

1. Generating a registry token from the Broadcom Support Portal
2. Configuring `~/.m2/settings.xml` with enterprise subscription credentials
3. Adding the enterprise Maven repository to `pom.xml`
4. Installing the `advisor` CLI for your OS/architecture
5. Running `advisor build-config get` and `advisor upgrade-plan get`
6. Interpreting upgrade plan output and handling blocked dependencies
7. Applying upgrades and opening PRs with `advisor upgrade-plan apply --push`
8. Creating a `.github/workflows/application-advisor.yml` workflow for CI
9. Running Broadcom commercial OpenRewrite recipes for Spring Boot 4.x directly

## Prerequisites

- A Broadcom Support Portal account with a **Tanzu Spring Enterprise**
  subscription
- Java 21+ and Maven (or Gradle) in the project
- Git repository (required for `--push` / PR creation)

## Installation

```bash
/plugin install application-advisor@claude-plugin-marketplace
```

## Resources

- [Application Advisor docs](https://techdocs.broadcom.com/us/en/vmware-tanzu/spring/application-advisor/1-6/app-advisor/what-is-app-advisor.html)
- [Generate a registry token](https://knowledge.broadcom.com/external/article/421110)
- [Enterprise artifact repository guide](https://techdocs.broadcom.com/us/en/vmware-tanzu/spring/tanzu-spring/commercial/spring-tanzu/guide-artifact-repository-developers.html)
