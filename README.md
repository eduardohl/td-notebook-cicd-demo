# td-notebook-cicd-demo

A tiny, working demo of **trunk-based CI/CD for Databricks notebooks** using
**GitHub Actions** + **Declarative Automation Bundles** (DABs, formerly
Databricks Asset Bundles).

The point: one versioned notebook is promoted `dev -> engineering -> prod`.
The code never changes between environments; only the bundle *target* changes
(workspace path, catalog/schema, and the identity that deploys and runs it).

> Demo simplification: all three "environments" live in a **single** Databricks
> workspace, separated by workspace path (`root_path`), a `catalog` variable,
> and a separate service principal per environment. In real life each target
> points to its own workspace and catalog.

## Layout

```
databricks.yml                      # bundle + 3 targets (dev/engineering/prod)
resources/silly_demo.job.yml        # the job that runs the notebook (serverless)
src/notebooks/hello.py              # the "silly" notebook
.github/workflows/notebook-cicd.yml # the pipeline
```

## Trunk-based flow

| Trigger | What happens |
|---|---|
| PR to `main` | `bundle validate --strict` only (nothing deployed) |
| Merge to `main` | One run for that commit: deploy + smoke-run **dev**, wait for lead approval, deploy + run **engineering**, wait for change-order approval, deploy + run **prod** |
| Manual `workflow_dispatch` on `main` | Re-runs the same full chain |

Environments can't be skipped. Each stage `needs` the one before it in the same
run, so prod only ever gets a commit that already passed dev and engineering.
Only `main` can deploy, enforced in three places: the workflow condition, a
branch policy on the `engineering` and `prod` GitHub environments, and
`git.branch: main` on the engineering/prod bundle targets (production mode
refuses other branches).

Short-lived feature branches off `main`, PR, merge, delete. `main` is always
releasable. Promotion moves one artifact forward; it does not move code between
branches.

## Developing in a Git folder

Developers work inside the Databricks workspace in a Git folder. The pipeline
deploys; the Git folder is only where the change is written. This follows the
[Git folders user flow](https://learn.microsoft.com/en-us/azure/databricks/repos/ci-cd)
and the [bundles-in-the-workspace guidance](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/workspace).

1. Link GitHub once: User Settings > Linked accounts (Git integration) > GitHub.
2. Clone this repo into your user folder as a Git folder
   (Workspace > Create > Git folder, or
   `databricks repos create https://github.com/<owner>/td-notebook-cicd-demo.git gitHub --path /Workspace/Users/<you>/td-notebook-cicd-demo`).
3. In the Git folder dialog, create your own branch from `main`.
4. Edit `src/notebooks/hello.py` and run it interactively. The widgets default
   to the dev values, so it runs as-is.
5. Optional: Databricks recognizes the folder as a bundle because
   `databricks.yml` is at the root. From the bundle panel you can deploy your
   personal **dev** copy (dev mode prefixes it with your name). Leave
   engineering and prod to the pipeline.
6. Commit and push from the Git folder dialog. Pull and push are always manual;
   nothing syncs to GitHub on its own.
7. Open a pull request to `main` on GitHub. From here the pipeline takes over.

Git folders are only used for development. Engineering and prod are deployed
by the pipeline from `main`, never from a Git folder.

## Identities and secrets

One service principal per environment. Each one deploys its environment and
its jobs run as it, so the dev identity cannot touch engineering or prod.

| Environment | Service principal | GitHub environment | Approval |
|---|---|---|---|
| dev | `cicd-demo-dev-sp` | `dev` | none (also used by PR checks) |
| engineering | `cicd-demo-engineering-sp` | `engineering` | lead approval, `main` only |
| prod | `cicd-demo-prod-sp` | `prod` | change-order approval, `main` only |

- `DATABRICKS_HOST` is a repo **variable** (not a secret).
- `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` are **environment
  secrets** on each GitHub environment. GitHub only releases a protected
  environment's secrets to a job after that environment's rules pass, so the
  prod credentials reach only `deploy-prod`, only from `main`, and only after
  approval. There are no repo-level Databricks secrets.
- Every deployed job is tagged with `git_sha` and `release_id`, so you can trace
  a production job back to its commit and pipeline run.

Next step up for a real setup: replace the secrets with
[workload identity federation](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/provider-github)
so GitHub's OIDC token signs in with no stored secret, bound to the GitHub
environment.

## Best practices applied

- Deployment modes: `development` on dev, `production` on engineering/prod.
- A separate service principal per environment; engineering/prod jobs `run_as` it.
- People get view-only permissions on engineering/prod jobs.
- `databricks/setup-cli` pinned to a release, not `@main`.
- `bundle validate --strict` on every PR.
- Concurrency control so two deploys to the same environment don't overlap.
- Required-reviewer approval on the engineering (lead) and prod (change order) environments.
- Promotion is one chained run per commit, so no environment can be skipped.

## Run it locally

```bash
databricks bundle validate --strict -t dev --profile <profile>
databricks bundle deploy -t dev --profile <profile>
databricks bundle run silly_demo -t dev --profile <profile>
```

Engineering and prod are deployed only by the pipeline, as their own
service principals.
