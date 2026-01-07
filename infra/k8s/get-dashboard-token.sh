#!/bin/bash

# Get Kubernetes Dashboard Access Token
# This script retrieves the admin user token for logging into the dashboard

set -e

echo "🔑 Kubernetes Dashboard Access Token"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if token file exists
if [ -f "dashboard-token.txt" ]; then
    echo "📄 Using saved token from dashboard-token.txt:"
    echo ""
    cat dashboard-token.txt
else
    echo "⚠️  Token file not found. Generating new token..."
    echo ""
    TOKEN=$(kubectl -n kubernetes-dashboard create token admin-user --duration=87600h 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo "$TOKEN" > dashboard-token.txt
        echo "$TOKEN"
    else
        echo "❌ Failed to create token. Make sure the admin-user service account exists."
        echo ""
        echo "To create it, run:"
        echo "  kubectl apply -f dashboard/dashboard-rbac.yaml"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 How to use this token:"
echo ""
echo "1. Start kubectl proxy:"
echo "   kubectl proxy"
echo ""
echo "2. Open the dashboard URL:"
echo "   http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/"
echo ""
echo "3. Select 'Token' and paste the token above"
echo ""
echo "Alternative access method (port-forward):"
echo "   kubectl port-forward -n kubernetes-dashboard service/kubernetes-dashboard 8443:443"
echo "   Then open: https://localhost:8443"
echo ""
echo "💡 Tip: The token is saved in dashboard-token.txt for future use"
