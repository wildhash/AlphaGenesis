#!/bin/bash
#
# Setup GCP Secret Manager for WEEX API Credentials
# Optional - only if you want maximum security
#

set -e

echo "======================================================================"
echo "  GCP Secret Manager Setup for WEEX API Credentials"
echo "======================================================================"
echo ""

# Check if gcloud is configured
if ! gcloud auth list 2>/dev/null | grep -q "ACTIVE"; then
    echo "Error: gcloud not authenticated"
    echo "Run: gcloud auth login"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Using project: $PROJECT_ID"
echo ""

# Enable Secret Manager API
echo "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com

echo ""
echo "Creating secrets..."
echo ""

# Create secrets (you'll be prompted to enter values)
echo "Enter your WEEX_API_KEY:"
read -s WEEX_API_KEY
echo "$WEEX_API_KEY" | gcloud secrets create weex-api-key --data-file=-

echo ""
echo "Enter your WEEX_API_SECRET:"
read -s WEEX_API_SECRET
echo "$WEEX_API_SECRET" | gcloud secrets create weex-api-secret --data-file=-

echo ""
echo "Enter your WEEX_API_PASSPHRASE:"
read -s WEEX_API_PASSPHRASE
echo "$WEEX_API_PASSPHRASE" | gcloud secrets create weex-api-passphrase --data-file=-

echo ""
echo "✓ Secrets created successfully!"
echo ""

# Grant access to compute service account
COMPUTE_SA="${PROJECT_ID}-compute@developer.gserviceaccount.com"

echo "Granting access to compute service account..."
gcloud secrets add-iam-policy-binding weex-api-key \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding weex-api-secret \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding weex-api-passphrase \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor"

echo "✓ Permissions granted!"
echo ""

# Create script to fetch secrets
cat > /opt/AlphaGenesis/fetch_secrets.sh << 'EOF'
#!/bin/bash
# Fetch secrets from GCP Secret Manager

WEEX_API_KEY=$(gcloud secrets versions access latest --secret="weex-api-key")
WEEX_API_SECRET=$(gcloud secrets versions access latest --secret="weex-api-secret")
WEEX_API_PASSPHRASE=$(gcloud secrets versions access latest --secret="weex-api-passphrase")

# Update .env file
cat > /opt/AlphaGenesis/.env << ENVEOF
WEEX_API_KEY=${WEEX_API_KEY}
WEEX_API_SECRET=${WEEX_API_SECRET}
WEEX_API_PASSPHRASE=${WEEX_API_PASSPHRASE}
WEEX_BASE_URL=https://api-contract.weex.com
INITIAL_CAPITAL=1000.0
UPDATE_INTERVAL=300
MODEL_DEVICE=cpu
MAX_LEVERAGE=20
LOG_LEVEL=INFO
ENABLE_LIVE_TRADING=true
ENVEOF

chmod 600 /opt/AlphaGenesis/.env
echo "✓ .env updated from secrets"
EOF

chmod +x /opt/AlphaGenesis/fetch_secrets.sh

echo "======================================================================"
echo "  Setup Complete!"
echo "======================================================================"
echo ""
echo "To update .env from secrets, run:"
echo "  bash /opt/AlphaGenesis/fetch_secrets.sh"
echo ""
echo "======================================================================"
