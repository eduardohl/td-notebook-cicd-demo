# td-notebook-cicd-demo

A tiny, working demo of **trunk-based CI/CD for Databricks notebooks** using
**GitHub Actions** + **Databricks Asset Bundles (DABs)**.

The point: one versioned notebook is promoted `dev -> qa -> pat -> prod`. The
code never changes between environments; only the bundle *target* changes
(workspace path + catalog/schema), injected as job parameters.

> Demo simplification: all three "environments" live in a **single** Databricks
> workspace, separated by workspace path (`root_path`) and a `catalog` variable.
> In real life each target points to a different workspace/profile and a
> different Unity Catalog.

## Layout

```
databricks.yml                      # bundle + 3 targets (dev/pat/prod)
resources/silly_demo.job.yml        # the job that runs the notebook (serverless)
src/notebooks/hello.py              # the "silly" notebook
.github/workflows/notebook-cicd.yml # the pipeline
```

## Trunk-based flow

| Trigger | What happens |
|---|---|
| PR to `main` | `bundle validate --strict` only (nothing deployed) |
| Merge to `main` | One run for that commit: deploy + smoke-run **dev**, wait for PAT approval, deploy + run **pat**, wait for prod approval, deploy + run **prod** |
| Manual `workflow_dispatch` on `main` | Re-runs the same full chain |

Environments can't be skipped. Each stage `needs` the one before it in the same
run, so prod only ever gets a commit that already passed dev and PAT. Only
`main` can deploy, enforced in three places: the workflow condition, a branch
policy on the `pat` and `prod` GitHub environments, and `git.branch: main` on
the pat/prod bundle targets (production mode refuses other branches).

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
   personal **dev** copy (dev mode prefixes it with your name). Leave pat and
   prod to the pipeline.
6. Commit and push from the Git folder dialog. Pull and push are always manual;
   nothing syncs to GitHub on its own.
7. Open a pull request to `main` on GitHub. From here the pipeline takes over.

Git folders are only used for development. PAT and prod are deployed by the
pipeline from `main`, never from a Git folder.

## Secrets required (repo settings)

CI authenticates as an OAuth service principal (Databricks-recommended for CI/CD):

- `DATABRICKS_HOST`: workspace URL, e.g. `https://xxx.cloud.databricks.com`
- `DATABRICKS_CLIENT_ID`: service principal application ID
- `DATABRICKS_CLIENT_SECRET`: service principal OAuth secret

The service principal needs workspace access, and `run_as` on the pat/prod
targets points at it so staging and prod jobs run as the SP, not a person.

## Best practices applied

- Deployment modes: `development` on dev, `production` on pat/prod.
- `run_as` a service principal on pat/prod.
- `databricks/setup-cli` pinned to a release, not `@main`.
- `bundle validate --strict` on every PR.
- Concurrency control so two deploys to the same environment don't overlap.
- Required-reviewer approval on the pat (QA sign-off) and prod (release) environments.
- Promotion is one chained run per commit, so no environment can be skipped.

## Run it locally

```bash
databricks bundle validate --strict -t dev --profile <profile>
databricks bundle deploy -t dev --profile <profile>
databricks bundle run silly_demo -t dev --profile <profile>
# promote the same artifact
databricks bundle deploy -t pat --profile <profile>
databricks bundle run silly_demo -t pat --profile <profile>
```
