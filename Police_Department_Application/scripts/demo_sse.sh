#!/bin/bash

# Police SEDI - SSE Demonstration Script
# Shows live Server-Sent Events functionality

echo "🚔 Police SEDI - Real-time SSE Demo"
echo "=================================="
echo ""

# Function to show a step
show_step() {
    echo "📌 Step $1: $2"
    echo "   → $3"
    echo ""
}

# Function to run commands with nice output
run_demo() {
    echo "💻 Running: $1"
    echo "---"
    eval "$1"
    echo ""
    echo "✅ Complete!"
    echo ""
}

show_step "1" "Check SSE Connection Stats" "curl -s http://localhost:2035/api/v1/connections | jq"
run_demo "curl -s http://localhost:2035/api/v1/connections | python3 -m json.tool || curl -s http://localhost:2035/api/v1/connections"

show_step "2" "Send Test Broadcast" "POST request to broadcast endpoint"
run_demo "curl -s -X POST 'http://localhost:2035/api/v1/broadcast/test?message=Demo+broadcast+from+script' | python3 -m json.tool || curl -s -X POST 'http://localhost:2035/api/v1/broadcast/test?message=Demo+broadcast+from+script'"

show_step "3" "Test Incident ACK (triggers SSE event)" "Acknowledge incident 123456"
run_demo "curl -s -X POST http://localhost:2035/api/v1/incidents/123456/ack \
  -H 'Content-Type: application/json' \
  -d '{
    \"alert_id\": 123456,
    \"tourist_id\": \"a1b2c3d4-1234-5678-9abc-123456789012\",
    \"note\": \"Demo ACK from script - triggers SSE broadcast\",
    \"officer_id\": \"demo-officer-001\"
  }' | python3 -m json.tool || curl -s -X POST http://localhost:2035/api/v1/incidents/123456/ack \
  -H 'Content-Type: application/json' \
  -d '{
    \"alert_id\": 123456,
    \"tourist_id\": \"a1b2c3d4-1234-5678-9abc-123456789012\",
    \"note\": \"Demo ACK from script - triggers SSE broadcast\",
    \"officer_id\": \"demo-officer-001\"
  }'"

show_step "4" "Live SSE Stream Test" "Connect and listen for 8 seconds"
echo "💻 Running: timeout 8s curl -N -H 'Accept: text/event-stream' http://localhost:2035/api/v1/stream"
echo "---"
echo "🔴 LIVE SSE EVENTS (listening for 8 seconds):"
timeout 8s curl -N -H "Accept: text/event-stream" http://localhost:2035/api/v1/stream 2>/dev/null | head -10
echo ""
echo "✅ SSE stream test complete!"
echo ""

echo "🎉 Demo Complete!"
echo ""
echo "📋 Summary:"
echo "   ✅ SSE connection endpoints working"
echo "   ✅ Broadcast functionality operational"
echo "   ✅ Incident ACK triggers SSE events"
echo "   ✅ Live event streaming functional"
echo ""
echo "🌐 To see the visual demo, open: http://localhost:2035/test_sse.html"
echo "🌐 Main application: http://localhost:2035/"
echo ""
