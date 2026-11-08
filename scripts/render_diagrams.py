import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGRAMS = {
    "architecture": r"""digraph G {
      graph [rankdir=TB, bgcolor="#f8fbf8", pad="0.4", fontsize=22,
             label="Cloud Tasks | local execution + AWS design", labelloc=t];
      node [shape=box, style="rounded,filled", fillcolor=white, color="#7aa991",
            fontname="DejaVu Sans", margin="0.2,0.15"];
      edge [fontname="DejaVu Sans", fontsize=10, color="#446856"];
      browser [label="Browser / static frontend"];
      actions [label="GitHub Actions CI\nTests / browser / SAM checks\nNo AWS access"];
      weather [label="External Open-Meteo\nHTTPS geocoding + current weather"];
      subgraph cluster_local {
        label="Implemented local path | loopback only"; color="#7aa991";
        localapi [label="Python local HTTP adapter\nSame Lambda handler / services / validation"];
        moto [label="Moto DynamoDB emulator\nDisposable demo data"];
      }
      subgraph cluster_aws {
        label="AWS design only | NOT deployed"; color="#c49a60";
        gateway [label="API Gateway HTTP API\nHTTPS / exact CORS / throttle"];
        lambda [label="Python 3.12 Lambda\nRouter / services / token checks"];
        db [label="DynamoDB\nUUID / conditional updates"];
        logs [label="CloudWatch\n14-day logs / metrics / alarms"];
        iam [label="Execution IAM role\nSpecific table CRUD + Scan\nWrite own log streams"];
      }
      browser -> localapi [label="HTTP + demo token"];
      localapi -> moto [label="boto3 / read + write"];
      localapi -> weather [label="HTTPS / timeout"];
      browser -> gateway [style=dashed,label="Designed HTTPS API requests"];
      gateway -> lambda [label="HTTP v2 event"];
      lambda -> db [label="AWS SDK / read + write"];
      lambda -> weather [style=dashed,label="Designed HTTPS integration"];
      lambda -> logs [label="status / latency / request ID"];
      gateway -> logs [label="access logs"];
      iam -> lambda [style=dashed,label="assumed role"];
      actions -> localapi [style=dotted,label="verify local HTTP + browser"];
    }""",
    "cicd": r"""digraph G {
      graph [rankdir=TB,bgcolor="#f8fbf8",pad="0.4",fontsize=22,
             label="CI workflow | AWS CD excluded",labelloc=t];
      node [shape=box,style="rounded,filled",fillcolor=white,color="#7aa991",
            fontname="DejaVu Sans",margin="0.2,0.15"];
      edge [fontname="DejaVu Sans",fontsize=10];
      trigger [label="Push / PR / manual dispatch"];
      quality [label="quality\nLint / pytest / audit\nSAM validate + build"];
      frontend [label="frontend\nChromium + local HTTP API + Moto\nCRUD / errors / mobile width"];
      weather [label="weather-live (advisory)\nReal HTTPS calls\nRecord PASS or BLOCKED"];
      results [label="Test results artifact"];
      shots [label="Frontend JSON + desktop/mobile screenshots"];
      live [label="Weather JSON artifact\nGreen workflow is NOT proof of live success"];
      trigger -> quality -> results;
      trigger -> frontend -> shots;
      trigger -> weather -> live;
    }""",
    "git-workflow": r"""digraph G {
      graph [rankdir=TB,bgcolor="#f8fbf8",pad="0.4",fontsize=22,
             label="GitHub Flow | solo demonstration",labelloc=t];
      node [shape=box,style="rounded,filled",fillcolor=white,color="#7aa991",
            fontname="DejaVu Sans",margin="0.2,0.15"];
      edge [fontname="DejaVu Sans",fontsize=10];
      main [label="main: stable baseline"];
      branch [label="feature / fix / docs branch"];
      pr [label="Pull Request: problem + result + evidence"];
      checks [label="CI + honest review record"];
      decision [shape=diamond,label="Checks and review acceptable?"];
      merge [label="Merge after review"];
      deliver [label="Deliver source / local demo\nNo AWS deployment"];
      revert [label="Revert via another PR if needed"];
      main -> branch -> pr -> checks -> decision;
      decision -> branch [label="revise"];
      decision -> merge [label="accept"];
      merge -> deliver -> revert;
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
