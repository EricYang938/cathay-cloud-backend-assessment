"""Regenerate exact architecture diagrams with Graphviz (dot required)."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = {
    "architecture": r"""digraph G {
      graph [rankdir=TB, bgcolor="#f8fbf8", pad="0.4", nodesep="0.5", ranksep="0.7",
             label="Cloud Task Management | AWS serverless demo",
             labelloc=t, fontsize=24, fontname="DejaVu Sans"];
      node [shape=box, style="rounded,filled", fillcolor="white", color="#b9cec2",
            fontname="DejaVu Sans", fontsize=13, margin="0.2,0.15"];
      edge [fontname="DejaVu Sans", fontsize=10, color="#446856"];
      browser [label="Browser / static frontend\nLocal :8080 (not cloud hosted)"];
      weather [label="External: Open-Meteo\nGeocoding + current weather"];
      github [label="GitHub Actions\nCI + opt-in CD (not run remotely)"];
      subgraph cluster_aws {
        label="AWS boundary | designed, NOT deployed"; color="#7aa991"; style=rounded;
        gateway [label="API Gateway HTTP API\nHTTPS / exact-origin CORS / throttle"];
        lambda [label="Python 3.12 Lambda\nValidation / services\nBearer demo token"];
        db [label="DynamoDB\nOn-demand / UUID key / atomic updates"];
        logs [label="CloudWatch\n14-day logs / metrics / alarms"];
        iam [label="Lambda IAM role\nTable CRUD + Scan only\nWrite own log streams only"];
        oidc [label="Existing OIDC deployment role\nRepository + environment scoped"];
        sam [label="SAM / CloudFormation\nDeploy template + artifacts"];
      }
      browser -> gateway [label="HTTPS + Bearer token"];
      gateway -> lambda [label="API requests / HTTP v2 event"];
      lambda -> db [label="AWS SDK / read + write"];
      lambda -> logs [label="status / latency / request ID"];
      gateway -> logs [label="access status / latency"];
      iam -> lambda [label="assumed execution role", style=dashed];
      lambda -> weather [label="HTTPS / bounded timeouts"];
      github -> oidc [label="OIDC federation (no access keys)"];
      oidc -> sam [label="authorized deployment"];
      sam -> lambda [label="build / update", style=dashed];
      sam -> gateway [style=dashed, label="provision"];
      sam -> db [style=dashed, label="provision"];
    }""",
    "cicd": r"""digraph G {
      graph [rankdir=TB, bgcolor="#f8fbf8", pad="0.4",
             label="CI / CD | configured, remote runs blocked",
             labelloc=t, fontsize=22];
      node [shape=box, style="rounded,filled", fillcolor=white, color="#7aa991",
            fontname="DejaVu Sans",
            margin="0.2,0.15"];
      edge [fontname="DejaVu Sans", fontsize=10];
      push [label="Push / Pull Request"];
      install [label="Python 3.12 / locked dependencies"];
      checks [label="Ruff lint + format / pytest\nSAM validate --lint + build"];
      artifacts [label="Upload test results"];
      deploytrigger [label="main push / manual dispatch"];
      verify [label="Re-run lint / tests / template validation"];
      gate [shape=diamond,label="ENABLE_AWS_DEPLOY=true\n+ main + aws-demo environment"];
      oidc [label="Existing scoped AWS OIDC role"];
      deploy [label="SAM build / deploy"];
      smoke [label="HTTP CRUD smoke test"];
      push -> install -> checks -> artifacts;
      deploytrigger -> verify -> gate;
      gate -> oidc [label="yes"];
      oidc -> deploy -> smoke;
      skip [label="Skip deployment (default)"];
      gate -> skip [label="no"];
    }""",
    "git-workflow": r"""digraph G {
      graph [rankdir=TB, bgcolor="#f8fbf8", pad="0.4",
             label="GitHub Flow | solo workflow design",
             labelloc=t, fontsize=22];
      node [shape=box, style="rounded,filled", fillcolor=white, color="#7aa991",
            fontname="DejaVu Sans",
            margin="0.2,0.15"];
      edge [fontname="DejaVu Sans", fontsize=10];
      main [label="main: stable baseline"];
      feature [label="feature / fix / docs branch"];
      pr [label="Pull Request: scope + evidence"];
      ci [label="CI + code review"];
      decision [shape=diamond,label="Checks pass?"];
      merge [label="Squash merge into main"];
      deploy [label="Opt-in deployment + smoke test"];
      rollback [label="Revert commit via PR / redeploy"];
      main -> feature -> pr -> ci -> decision;
      decision -> feature [label="revise"];
      decision -> merge [label="approve"];
      merge -> deploy -> rollback;
    }""",
}

if __name__ == "__main__":
    for name, source in DIAGRAMS.items():
        dot = ROOT / "docs" / f"{name}.dot"
        dot.write_text(source)
        for kind in ("png", "svg"):
            subprocess.run(
                ["dot", f"-T{kind}", str(dot), "-o", str(dot.with_suffix("." + kind))], check=True
            )
        print("Rendered", name)
