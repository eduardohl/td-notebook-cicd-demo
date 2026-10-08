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
| Manual `workflow_dispatch` | Pick `qa` / `pat` / `prod` to promote the same commit |
| GitHub Release published | Deploy the **prod** target |

Short-lived feature branches off `main`, PR, merge, delete. `main` is always
releasable. Promotion moves one artifact forward; it does not move code between
branches.

## Secrets required (repo settings)

- `DATABRICKS_HOST` — workspace URL, e.g. `https://xxx.cloud.databricks.com`
- `DATABRICKS_TOKEN` — a Databricks PAT

## Run it locally

```bash
databricks bundle validate -t dev   --profile <profile>
databricks bundle deploy   -t dev   --profile <profile>
databricks bundle run      silly_demo -t dev --profile <profile>
# promote the same artifact
databricks bundle deploy   -t qa    --profile <profile>
databricks bundle run      silly_demo -t qa --profile <profile>
```
