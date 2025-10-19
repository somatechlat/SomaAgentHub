#!/bin/bash

# Marketing Campaign Wizard Demo
# This script demonstrates the full wizard flow end-to-end

BASE_URL="http://localhost:10000"

echo "🎯 SomaAgentHub Marketing Campaign Wizard Demo"
echo "=============================================="
echo ""

# Step 1: List wizards
echo "📋 Step 1: List available wizards"
curl -s $BASE_URL/v1/wizards | jq .
echo ""

# Step 2: Start wizard
echo "🚀 Step 2: Start marketing campaign wizard"
SESSION_ID=$(curl -s -X POST $BASE_URL/v1/wizards/start \
  -H "Content-Type: application/json" \
  -d '{"wizard_id":"marketing_campaign_v1","user_id":"demo-agent"}' | jq -r .session_id)

echo "✅ Session ID: $SESSION_ID"
echo ""

# Step 3: Answer Question 1 - Campaign Name
echo "📝 Step 3: Answer Q1 - Campaign Name"
curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":"Fall 2025 AI Platform Launch"}' | jq .question
echo ""

# Step 4: Answer Question 2 - Campaign Type
echo "📝 Step 4: Answer Q2 - Campaign Type"
curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":"product_launch"}' | jq .question
echo ""

# Step 5: Answer Question 3 - Target Audience
echo "📝 Step 5: Answer Q3 - Target Audience"
curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":"Enterprise CTOs, DevOps Engineers, AI/ML Teams"}' | jq .question
echo ""

# Step 6: Answer Question 4 - Channels
echo "📝 Step 6: Answer Q4 - Channels"
curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":["email","blog","social_linkedin","social_twitter"]}' | jq .question
echo ""

# Step 7: Answer Question 5 - Launch Date
echo "📝 Step 7: Answer Q5 - Launch Date"
curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":"2025-10-21"}' | jq .question
echo ""

# Step 8: Answer Question 6 - Budget
echo "📝 Step 8: Answer Q6 - Budget"
curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":10000}' | jq .question
echo ""

# Step 9: Answer Question 7 - Key Messages
echo "📝 Step 9: Answer Q7 - Key Messages"
curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":"Revolutionary AI agent platform. 10x faster deployment. Enterprise-grade security. Open-source foundation."}' | jq .question
echo ""

# Step 10: Answer Question 8 - Success Metrics
echo "📝 Step 10: Answer Q8 - Success Metrics"
curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":["impressions","clicks","leads","signups","engagement"]}' | jq .question
echo ""

# Step 11: Answer Question 9 - Brand Voice
echo "📝 Step 11: Answer Q9 - Brand Voice"
curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":"professional"}' | jq .question
echo ""

# Step 12: Answer Question 10 - Approval Required
echo "📝 Step 12: Answer Q10 - Approval Required"
COMPLETION=$(curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/answer \
  -H "Content-Type: application/json" \
  -d '{"value":true}')

echo "$COMPLETION" | jq .
echo ""

# Step 13: Check if wizard is completed
IS_COMPLETED=$(echo "$COMPLETION" | jq -r .completed)

if [ "$IS_COMPLETED" == "true" ]; then
  echo "✨ Wizard completed successfully!"
  echo ""
  
  echo "📊 Execution Plan:"
  echo "$COMPLETION" | jq .execution_plan
  echo ""
  
  echo "🎯 Next Steps:"
  echo "$COMPLETION" | jq .next_steps
  echo ""
  
  # Step 14: Approve execution
  echo "✅ Step 14: Approve and execute campaign"
  curl -s -X POST $BASE_URL/v1/wizards/$SESSION_ID/approve \
    -H "Content-Type: application/json" | jq .
  echo ""
  
  echo "🎉 Campaign automation queued for execution!"
else
  echo "❌ Wizard not completed. Current progress:"
  echo "$COMPLETION" | jq .progress
fi

echo ""
echo "=============================================="
echo "✅ Demo Complete! Session ID: $SESSION_ID"
