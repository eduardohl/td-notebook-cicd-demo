# td-notebook-cicd-demo

A tiny, working demo of **trunk-based CI/CD for Databricks notebooks** using
**GitHub Actions** + **Databricks Asset Bundles (DABs)**.

The point: one versioned notebook is promoted `dev -> qa -> pat -> prod`. The
code never changes between environments; only the bundle *target* changes
(workspace path + catalog/schema), injected as job parameters.

> Demo simplification: all four "environments" live in a **single** Databricks
> workspace, separated by workspace path (`root_path`) and a `catalog` variable.
> In real life each target points to a different workspace/profile and a
> different Unity Catalog.

## Layout

```
databricks.yml                      # bundle + 4 targets (dev/qa/pat/prod)
resources/silly_demo.job.yml        # the job that runs the notebook (serverless)
src/notebooks/hello.py              # the "silly" notebook
.github/workflows/notebook-cicd.yml # the pipeline
```

## Trunk-based flow

| Trigger | What happens |
|---|---|
| PR to `main` | `bundle validate` only (nothing deployed) |
| Merge to `main` | Auto deploy + smoke-run the **dev** target |
| Manual `workflow_dispatch` | Pick `pat` / `prod` to promote the same commit |
| GitHub Release published | Deploy the **prod** target |

Short-lived feature branches off `main`, PR, merge, delete. `main` is always
releasable. Promotion moves one artifact forward; it does not move code between
branches.

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
- Concurrency control so deploys to the same ref don't overlap.
- Required-reviewer approval on the prod environment.

## Run it locally

```bash
databricks bundle validate --strict -t dev --profile <profile>
databricks bundle deploy -t dev --profile <profile>
databricks bundle run silly_demo -t dev --profile <profile>
# promote the same artifact
databricks bundle deploy -t pat --profile <profile>
databricks bundle run silly_demo -t pat --profile <profile>
```
