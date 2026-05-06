#!/bin/bash
# ═══════════════════════════════════════════════════════════
# BNX Convertidor — CLI Quick Reference
# ═══════════════════════════════════════════════════════════

CMD=$1
shift

case "$CMD" in

  # ── Compilar grafos ──────────────────────────────────────
  glue)
    echo "🔧 Compiling to AWS Glue..."
    python3 main.py --project "$1" --xfr "$2" --target glue --output "${3:-output_glue.py}"
    ;;
  spark)
    echo "⚡ Compiling to PySpark..."
    python3 main.py --project "$1" --xfr "$2" --target spark --output "${3:-output_spark.py}"
    ;;
  flink)
    echo "🌊 Compiling to Apache Flink..."
    python3 main.py --project "$1" --xfr "$2" --target flink --output "${3:-output_flink.py}"
    ;;

  # ── Compilar con DML ─────────────────────────────────────
  full)
    echo "🚀 Full compile (MP + XFR + DML)..."
    python3 main.py --project "$1" --xfr "$2" --dml "$3" --target "${4:-glue}" --output "${5:-output.py}"
    ;;

  # ── Samples rápidos ──────────────────────────────────────
  test)
    echo "🧪 Running test graph (e2e)..."
    python3 main.py --project e2e/test.mp --xfr e2e/test.xfr --target "${1:-glue}" --output output_test.py
    ;;
  scan)
    echo "📅 Running scan/dates test..."
    python3 main.py --project samples/scan_dates/scan_test.mp --xfr samples/scan_dates/scan_test.xfr --target "${1:-glue}" --output output_scan.py
    ;;
  native)
    echo "🏦 Running native Ab Initio graph..."
    python3 main.py --project samples/abinitio_native/fraud_detection.mp --target "${1:-glue}" --output output_native.py
    ;;
  monster)
    echo "👹 Running monster banking graph (45 nodes)..."
    python3 main.py --project samples/abinitio_native/monster_banking.mp --target "${1:-glue}" --output output_monster.py
    ;;

  # ── Deploy ───────────────────────────────────────────────
  deploy-lambda)
    echo "⚡ Deploying Lambda..."
    zip -r lambda_package.zip lambda/handler.py src/ -x "src/__pycache__/*" "src/**/__pycache__/*"
    aws lambda update-function-code --function-name bnx-compiler --zip-file fileb://lambda_package.zip --region us-east-1
    echo "✅ Lambda deployed"
    ;;
  deploy-ui)
    echo "☁️ Deploying UI (git push → Amplify)..."
    git add -A
    git commit -m "deploy: update" 2>/dev/null || true
    git push
    echo "✅ Pushed to Amplify"
    ;;
  deploy-all)
    echo "🚀 Deploying everything..."
    $0 deploy-lambda
    $0 deploy-ui
    ;;

  # ── Dev local ────────────────────────────────────────────
  dev)
    echo "🖥️ Starting local dev server..."
    cd ui && npm run dev
    ;;
  api)
    echo "🌐 Starting local API..."
    uvicorn api.server:app --reload --port 8000
    ;;

  # ── Help ─────────────────────────────────────────────────
  *)
    echo "🚀 BNX Convertidor CLI"
    echo "═══════════════════════════════════════"
    echo ""
    echo "COMPILAR:"
    echo "  ./bnx.sh glue graph.mp rules.xfr [output.py]"
    echo "  ./bnx.sh spark graph.mp rules.xfr [output.py]"
    echo "  ./bnx.sh flink graph.mp rules.xfr [output.py]"
    echo "  ./bnx.sh full graph.mp rules.xfr schema.dml [target] [output.py]"
    echo ""
    echo "SAMPLES:"
    echo "  ./bnx.sh test [glue|spark|flink]     — e2e test graph"
    echo "  ./bnx.sh scan [glue|spark|flink]     — scan + dates test"
    echo "  ./bnx.sh native [glue|spark|flink]   — native Ab Initio"
    echo "  ./bnx.sh monster [glue|spark|flink]  — 45 node monster"
    echo ""
    echo "DEPLOY:"
    echo "  ./bnx.sh deploy-lambda    — zip + update Lambda"
    echo "  ./bnx.sh deploy-ui        — git push → Amplify"
    echo "  ./bnx.sh deploy-all       — Lambda + UI"
    echo ""
    echo "DEV:"
    echo "  ./bnx.sh dev              — start React dev server"
    echo "  ./bnx.sh api              — start FastAPI local"
    echo ""
    ;;
esac
