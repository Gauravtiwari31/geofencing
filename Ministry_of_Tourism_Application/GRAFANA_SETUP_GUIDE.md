# 📊 Grafana Dashboard Setup Guide for MoD Core

## 🎯 Quick Access
- **Grafana URL:** `http://localhost:2029` (after port forwarding)
- **Username:** `admin`
- **Password:** `admin123`

## 🚀 Setup Steps

### 1. **Access Grafana**
1. Open your browser and navigate to Grafana
2. Login with the credentials above
3. You may be prompted to change the password (optional)

### 2. **Add Prometheus Data Source** (Manual Method)
If auto-provisioning doesn't work:

1. Click the **gear icon** (⚙️) in the sidebar → **Data Sources**
2. Click **"Add data source"**
3. Select **"Prometheus"**
4. Configure:
   - **Name:** `Prometheus`
   - **URL:** `http://localhost:2028`
   - **Access:** `Server (default)`
5. Click **"Save & Test"**

### 3. **Import MoD Core Dashboard**

#### Option A: Auto-provisioned (Recommended)
The dashboard should automatically appear in the **"MoD Core"** folder if Grafana is configured correctly.

#### Option B: Manual Import
1. Click the **"+"** icon in sidebar → **Import**
2. Upload the file: `/workspace/configs/grafana/dashboards/mod-core-operational.json`
3. Or copy-paste the JSON content from that file
4. Click **"Load"** → **"Import"**

## 📈 **Dashboard Features**

### **MoD Core Operational Dashboard**
- **🚨 SOS Alerts:** Real-time emergency alerts
- **👥 Active Tourists:** Current tourist count
- **🗺️ Geofence Violations:** Boundary breach monitoring
- **📱 Device Status:** Battery levels and connectivity
- **⚡ API Performance:** Response times and request rates
- **🔴 Red Zone Proximity:** Tourists near restricted areas

## 🎛️ **Dashboard Panels Explained**

### **Critical Metrics:**
1. **API Request Rate** - Requests per second
2. **API Response Time** - 95th percentile latency
3. **Active SOS Alerts** - Emergency situations (should be 0!)
4. **Active Tourists** - Total monitored individuals
5. **Tourists Near Red Zones** - Security concern indicator
6. **Low Battery Devices** - Devices needing attention
7. **Geofence Violations** - Boundary breach rates

### **Alert Thresholds:**
- 🟢 **Green:** Normal operation
- 🟡 **Yellow:** Warning condition
- 🔴 **Red:** Critical situation requiring attention

## 🔧 **Troubleshooting**

### **No Data Showing?**
1. **Check Prometheus:** Ensure it's running on port 2028
2. **Check Data Source:** Verify Prometheus connection in Grafana
3. **Check Metrics:** Visit `http://localhost:8000/metrics` to see if FastAPI is exposing metrics

### **Can't Access Grafana?**
1. **Check Service:** Ensure Grafana is running in supervisor
2. **Check Port:** Verify port 2029 is accessible
3. **Check Logs:** Use supervisor to check Grafana logs

### **Dashboard Not Loading?**
1. **Check Provisioning:** Ensure `/workspace/configs/grafana/provisioning` is accessible
2. **Restart Grafana:** Use supervisor to restart the service
3. **Manual Import:** Use Option B above to manually import

## 🎯 **Custom Dashboards**

You can create additional dashboards for:
- **📍 Tourist Locations** - Geographic distribution
- **🏥 Health Monitoring** - Vitals and medical alerts
- **👮 Police Activity** - SEDI monitoring statistics
- **🔐 Security Events** - Authentication and access logs
- **📊 System Performance** - Container resource usage

## 📚 **Key Grafana Features to Explore**

1. **Time Range Selector** - View different time periods
2. **Refresh Controls** - Auto-refresh for real-time monitoring
3. **Panel Drill-down** - Click on metrics for detailed views
4. **Alerting** - Set up notifications for critical events
5. **Annotations** - Mark important events on graphs
6. **Variables** - Filter data by tourist, location, etc.

## 🚨 **Emergency Response Dashboard**

For critical situations, focus on:
- **SOS Alerts panel** - Must remain at 0
- **Red Zone proximity** - Immediate security concern
- **API response time** - System performance during crisis
- **Device connectivity** - Communication capability

---

**🎉 Your MoD Core monitoring system is now fully operational with professional-grade dashboards!**
