# backend/demo_analytics_api.py
"""
StudySprint 4.0 - Analytics API Demo
Demonstration of analytics API endpoints
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"


def demo_analytics_endpoints():
    """Demonstrate analytics API endpoints"""
    print("🎬 StudySprint 4.0 Analytics API Demo")
    print("=" * 50)
    
    # Demo 1: Reading Speed Analytics
    print("\n📈 1. Reading Speed Analytics")
    try:
        response = requests.get(f"{BASE_URL}/analytics/reading-speed?days=30")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved reading speed data:")
            print(f"   Sessions analyzed: {data.get('session_count', 'N/A')}")
            print(f"   Average speed: {data.get('speed_statistics', {}).get('average_pages_per_minute', 'N/A'):.2f} pages/min")
            print(f"   Speed consistency: {data.get('speed_statistics', {}).get('speed_consistency', 'N/A'):.2f}")
        else:
            print(f"⚠️ Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 2: Performance Trends
    print("\n📊 2. Performance Trends")
    try:
        response = requests.get(f"{BASE_URL}/analytics/performance-trends?days=14")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved performance trends:")
            print(f"   Data points: {data.get('data_points', 'N/A')}")
            print(f"   Average productivity: {data.get('averages', {}).get('productivity_score', 'N/A'):.2f}")
            print(f"   Overall trend: {data.get('improvement_indicators', {}).get('overall_trend', 'N/A')}")
        else:
            print(f"⚠️ Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 3: Learning Velocity
    print("\n🚀 3. Learning Velocity")
    try:
        response = requests.get(f"{BASE_URL}/analytics/learning-velocity?days=21")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved learning velocity:")
            print(f"   Total pages covered: {data.get('total_pages_covered', 'N/A')}")
            print(f"   Pages per day: {data.get('velocity_metrics', {}).get('pages_per_day', 'N/A'):.1f}")
            print(f"   Velocity trend: {data.get('velocity_trend', {}).get('direction', 'N/A')}")
        else:
            print(f"⚠️ Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 4: Bottleneck Analysis
    print("\n🔍 4. Bottleneck Analysis")
    try:
        response = requests.get(f"{BASE_URL}/analytics/bottlenecks?days=30")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved bottleneck analysis:")
            print(f"   Overall health: {data.get('overall_health', 'N/A')}")
            print(f"   Bottlenecks found: {data.get('bottlenecks_found', 'N/A')}")
            bottlenecks = data.get('bottlenecks', [])
            for i, bottleneck in enumerate(bottlenecks[:3]):  # Show first 3
                print(f"   {i+1}. {bottleneck.get('type', 'Unknown')} ({bottleneck.get('severity', 'Unknown')})")
        else:
            print(f"⚠️ Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Demo 5: Optimization Suggestions
    print("\n💡 5. Optimization Suggestions")
    try:
        response = requests.get(f"{BASE_URL}/analytics/optimization-suggestions?days=7")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Retrieved optimization suggestions:")
            suggestions = data.get('suggestions', [])
            for i, suggestion in enumerate(suggestions[:5]):  # Show first 5
                print(f"   {i+1}. {suggestion}")
        else:
            print(f"⚠️ Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Analytics API Demo Complete!")
    print("\n📚 Available Endpoints:")
    print("   📈 /api/analytics/reading-speed - Reading speed trends")
    print("   📊 /api/analytics/performance-trends - Productivity analysis")
    print("   🚀 /api/analytics/learning-velocity - Learning progress rate")
    print("   🔍 /api/analytics/bottlenecks - Performance bottlenecks")
    print("   💡 /api/analytics/optimization-suggestions - AI recommendations")
    print("   📋 /api/analytics/sessions/{id}/analytics - Session analysis")
    print("   🎯 /api/analytics/sessions/{id}/focus-analysis - Focus patterns")


if __name__ == "__main__":
    print("🚨 Make sure the StudySprint server is running first!")
    print("   Run: ./run_stage3.sh")
    print("   Then press Enter to continue...")
    input()
    
    demo_analytics_endpoints()