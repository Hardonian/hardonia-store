#!/bin/bash
# Sovereign AI Health Score — One-command install
# Usage: curl -fsSL https://aiautomatedsystems.ca/install/trust-score.sh | bash

set -euo pipefail

INSTALL_DIR="${HOME}/.local/share/sovereign-trust-score"
BIN_DIR="${HOME}/.local/bin"
REPO_DIR="/home/scott/hardonia.store/products/sovereign-ai-health-score"

echo "🔒 Installing Sovereign AI Health Score..."

# Create directories
mkdir -p "${INSTALL_DIR}/engine" "${BIN_DIR}"

# Copy engine
cp -r "${REPO_DIR}/engine" "${INSTALL_DIR}/"
cp "${REPO_DIR}/template.md" "${INSTALL_DIR}/README.md"
cp "${REPO_DIR}/product.json" "${INSTALL_DIR}/product.json"

# Create wrapper script
cat > "${BIN_DIR}/trust-score" << 'EOF'
#!/bin/bash
cd /home/scott/hardonia.store/products/sovereign-ai-health-score/engine
python3 trust_score.py "$@"
EOF
chmod +x "${BIN_DIR}/trust-score"

# Verify
if "${BIN_DIR}/trust-score" --self >/dev/null 2>&1; then
    echo "✅ trust-score installed and self-verification passed"
else
    echo "⚠️  trust-score installed but self-verification has findings (expected on fresh install)"
    echo "   Run 'trust-score --self' to see your live score"
fi

echo ""
echo "Usage:"
echo "  trust-score --self     # Run self-verification, shows your live score"
echo "  trust-score --json     # Machine-readable output for automation"
echo "  trust-score            # Human-readable summary"
echo ""
echo "Monthly cron (add to crontab):"
echo "  0 6 1 * * ${BIN_DIR}/trust-score --json > ~/trust-score-\$(date +%Y-%m).json"
echo ""
echo "Landing page: https://aiautomatedsystems.ca/p/sovereign-ai-health-score"
echo "Checkout: https://buy.stripe.com/6oU00ibvOeOogVs2Yhb3q2J"
