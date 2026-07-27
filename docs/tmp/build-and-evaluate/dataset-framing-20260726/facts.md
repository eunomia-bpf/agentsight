# Dataset framing fact check

Date: 2026-07-26 PDT (GitHub queries ran on 2026-07-27 UTC)

Scope: the six cases in
`docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/projects.json`
(SHA-256
`2b2b38560c5d9e0c0a7f9ae0cf37dbea73d2bd1d919c78f127f23f3c5a4901bf`).
This file contains identifying evidence for internal audit.  The paper uses
anonymous case labels only.

## Definitions

- **Public open-source case:** GitHub reports `visibility=public` and the
  repository metadata exposes an OSI license identifier.  In this snapshot,
  every qualifying case reports `MIT`.
- **Verified active maintainer:** a GitHub account that (1) currently has the
  repository role `admin` or `maintain`, and (2) has at least one
  GitHub-linked commit in the case's included-session event window.  Commit
  queries use the frozen revision from `projects.json` when GitHub accepts it;
  where GitHub returned HTTP 500 for that revision, the default-branch query
  used the same closed time window and was reconciled against the frozen local
  revision.  `write` collaborators, bots, external contributors, unlinked Git
  signatures, and accounts with permission but no linked commit in the window
  are not counted.
- **Session time:** for each admitted `native_session_id`, its start is the
  minimum `ts_ms` among that session's included Tool events.  A case span is
  the earliest to latest such session start.  Months below use
  30.436875 days/month and are descriptive approximations.

The maintainer definition is deliberately conservative.  It verifies both
current maintainer authority and activity, but it does not reconstruct
historical permission changes.  In particular, one ActPlane commit has the
unlinked author signature `Mao Wenan <wenan.mwa@alibaba-inc.com>` while a
similarly named current admin account exists; GitHub returns `author=null`, so
that account is not counted without a verifiable identity link.

## Repository visibility, license, and stars

GitHub metadata snapshot: **2026-07-27T01:01:26Z**
(2026-07-26T18:01:26-07:00).

| Frozen case | GitHub repository | Visibility | License | Stars |
|---|---|---:|---:|---:|
| agentsight | `eunomia-bpf/agentsight` | public | MIT | 546 |
| ActPlane | `eunomia-bpf/ActPlane` | public | MIT | 79 |
| bpf-developer-tutorial | `eunomia-bpf/bpf-developer-tutorial` | public | MIT | 4,201 |
| eunomia.dev | `eunomia-bpf/eunomia.dev` | public | MIT | 227 |
| agentskill-observability-paper | `eunomia-bpf/agentskill-observability-paper` | private | no public license metadata | 0 |
| academic-writing-skills | `yunwei37/academic-writing-skills` | private | no public license metadata | 0 |

Thus, **4/6 cases are verified public open-source repositories and 2/6 are
private author-associated repositories**.  The four public cases sum to
**5,053 repository stars**.

The four public cases belong to the same GitHub organization.  At the same
snapshot, the organization API returned **144 public repositories whose
individual `stargazers_count` values sum to 9,924**.  GitHub does not expose an
organization-level star metric: 9,924 is an aggregate repository-star count,
not a count of unique users, and a user may star multiple repositories.

Evidence:

- Repository metadata endpoints:
  `https://api.github.com/repos/eunomia-bpf/agentsight`,
  `https://api.github.com/repos/eunomia-bpf/ActPlane`,
  `https://api.github.com/repos/eunomia-bpf/bpf-developer-tutorial`,
  `https://api.github.com/repos/eunomia-bpf/eunomia.dev`,
  `https://api.github.com/repos/eunomia-bpf/agentskill-observability-paper`,
  and `https://api.github.com/repos/yunwei37/academic-writing-skills`.
- Community aggregate endpoint:
  `https://api.github.com/orgs/eunomia-bpf/repos?type=public&per_page=100`,
  fetched with `gh api --paginate`; the returned
  `stargazers_count` values were summed with `jq`.
- Reproduction:

  ```bash
  for repo in \
    eunomia-bpf/agentsight eunomia-bpf/ActPlane \
    eunomia-bpf/bpf-developer-tutorial eunomia-bpf/eunomia.dev \
    eunomia-bpf/agentskill-observability-paper \
    yunwei37/academic-writing-skills
  do
    gh api "repos/$repo" \
      --jq '{full_name,visibility,private,license:(.license.spdx_id // null),stargazers_count}'
  done

  gh api --paginate 'orgs/eunomia-bpf/repos?type=public&per_page=100' \
    --jq '[.[] | {full_name,stargazers_count}]' |
    jq -s 'add | {public_repository_count:length,
      aggregate_repository_stars:(map(.stargazers_count)|add)}'
  ```

## Verified active maintainers

Permission and commit endpoints were queried between
**2026-07-27T01:00:14Z and 2026-07-27T01:04:36Z**.

| Frozen case | Included-event window (UTC) | Verified active maintainer accounts | Count |
|---|---|---|---:|
| agentsight | 2026-03-06T01:49:04Z--2026-07-22T08:22:47Z | `Littlefisher619`, `yunwei37` | 2 |
| ActPlane | 2026-05-23T04:56:36Z--2026-07-18T08:42:11Z | `Littlefisher619`, `Officeyutong`, `yunwei37` | 3 |
| bpf-developer-tutorial | 2026-01-11T09:51:30Z--2026-07-22T04:46:07Z | `Littlefisher619`, `yunwei37` | 2 |
| eunomia.dev | 2026-03-06T20:23:00Z--2026-07-22T08:21:49Z | `Littlefisher619`, `yunwei37` | 2 |
| agentskill-observability-paper | 2026-07-12T04:16:55Z--2026-07-12T07:42:11Z | `Littlefisher619` | 1 |
| academic-writing-skills | 2026-06-13T16:12:17Z--2026-07-16T02:59:27Z | `yunwei37` | 1 |

The four public cases therefore have **2--3 verified active maintainers per
repository (median 2)** and **three distinct verified active maintainer
accounts in their union**.  The two private cases each have one under the same
definition.  Across all six cases, the per-repository range is **1--3** and
the median is **2**.

Evidence:

- Current roles:
  `GET /repos/{owner}/{repo}/collaborators?affiliation=all&per_page=100`,
  retaining `role_name` equal to `admin` or `maintain`.
- Windowed activity:
  `GET /repos/{owner}/{repo}/commits?sha={frozen_revision}&author={login}&since={start}&until={end}&per_page=100`.
  GitHub returned HTTP 500 with an empty body for the frozen-revision commit
  query on bpf-developer-tutorial and agentskill-observability-paper.  For
  those repositories, the same author/time query without `sha` returned 4 and
  11 linked commits for the two active tutorial maintainers and 12 for the
  active paper-repository maintainer.  Local
  `git log {frozen_revision} --since=... --until=...` has the same linked
  human signatures and no later-in-window frozen-history discrepancy.
- Per-account linked-commit counts used for the positive classifications:
  agentsight 60/74; ActPlane 98/1/19; bpf-developer-tutorial 4/11;
  eunomia.dev 59/25; agentskill-observability-paper 12; and
  academic-writing-skills 1, in the account order shown in the table.
- Reproduction pattern:

  ```bash
  gh api --paginate \
    'repos/OWNER/REPO/collaborators?affiliation=all&per_page=100' \
    --jq '.[] | select(.role_name=="admin" or .role_name=="maintain") |
      [.login,.role_name] | @tsv'

  gh api --paginate --method GET 'repos/OWNER/REPO/commits' \
    -f sha=FROZEN_REVISION -f author=LOGIN \
    -f since=WINDOW_START -f until=WINDOW_END -f per_page=100 \
    --jq '.[].sha'
  ```

## Session-start spans from the final-HEAD corpus

The six event files contain **551 distinct admitted native root sessions**,
matching the paper corpus total.

| Frozen case | Native roots | Earliest session start (UTC) | Latest session start (UTC) | Span (days) | Approx. months |
|---|---:|---|---|---:|---:|
| agentsight | 301 | 2026-03-06T01:49:04Z | 2026-07-20T05:52:48Z | 136.169 | 4.474 |
| ActPlane | 139 | 2026-05-23T04:56:36Z | 2026-07-18T07:40:54Z | 56.114 | 1.844 |
| bpf-developer-tutorial | 35 | 2026-01-11T09:51:30Z | 2026-07-22T04:11:16Z | 191.764 | 6.300 |
| eunomia.dev | 51 | 2026-03-06T20:23:00Z | 2026-07-19T04:49:23Z | 134.352 | 4.414 |
| agentskill-observability-paper | 8 | 2026-07-12T04:16:55Z | 2026-07-12T07:19:59Z | 0.127 | 0.004 |
| academic-writing-skills | 17 | 2026-06-13T16:12:17Z | 2026-07-16T01:53:20Z | 32.404 | 1.065 |
| **Overall** | **551** | **2026-01-11T09:51:30Z** | **2026-07-22T04:11:16Z** | **191.764** | **6.300** |

The overall session-start envelope is 191 days, 18 hours, 19 minutes, and
46 seconds: **about 6.3 months**, so “about half a year” is supported for the
combined corpus.  It is not supported for every project individually: only
the tutorial case spans more than six months, while the other cases span from
about three hours to about 4.5 months.

Evidence:

- Final-HEAD event files:
  `docs/tmp/build-and-evaluate/rq1-rq4-recompute-final/rq1-raw/events/*.json`.
- Frozen gzip SHA-256 values, in case-name order:
  agentsight
  `b2301390a9f665480a8efd87690653064ca989bfc4a3793d54ea7798793bc01b`;
  ActPlane
  `7cee0b947d9cae85263894059674b069ec173d41907c9ba01938becaaa493ea2`;
  bpf-developer-tutorial
  `0fe42215ca4aa6b28676a155608a6ce71bc6d2c38a921e918a0f76bfdf472b8b`;
  eunomia.dev
  `f547f0607bfb2d81cc923f9292b34463cb4cd9a6054392d66268cf11869fd21e`;
  agentskill-observability-paper
  `c5a866cc256458ae7cd75a570e537ddf66f9e8d12977a1bfd89546dce006a4ab`;
  academic-writing-skills
  `04e5da6d202649d221e563bfb6bab21c51e9a5d4bfcccfdb55a1ee9e467c4d83`.
- Calculation pattern:

  ```bash
  jq -r '.events[] | [.native_session_id, .ts_ms] | @tsv' CASE.json |
    LC_ALL=C sort -k1,1 -k2,2n
  ```

  The sorted rows are reduced to one minimum `ts_ms` per
  `native_session_id`; case and overall minima/maxima are then converted from
  Unix milliseconds to UTC.  As a cross-check, the maximum included Tool
  timestamp for each case matches `observation_end_ms` in `projects.json`.

## Framing decision and discrepancy from the requested wording

The requested phrase cannot be used literally:

1. **“over 10K stars” is not verified.**  The relevant community snapshot is
   9,924 aggregate repository stars, 76 below 10,000.  The paper may say
   “about 9.9K aggregate GitHub repository stars,” but not “over 10K.”
2. **Not all six cases are public open source.**  Four are public MIT
   repositories in that community; two are private author-associated
   repositories.
3. **“2--3 developers” is true only for the four public cases under the
   verified-active-maintainer definition.**  The two private cases each have
   one; the all-case range is 1--3.
4. **“about half a year” is true for the combined corpus**, whose admitted
   session starts span about 6.3 months.  It is not a per-project statement.

Paper revision outline: identify six anonymous author-associated local cases;
state the 4-public/2-private composition; report the community as about 9.9K
aggregate repository stars; state 2--3 verified active maintainers for the
public cases and one for each private case; report the combined 191.8-day
(about 6.3-month) session-start span; preserve every RQ, estimand, and existing
result number.
