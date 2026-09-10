package com.landslide.backend.dto;

public class RiskZoneLocationResponse {

    private boolean insideRiskZone;
    private RiskZoneResponse riskZone;

    public RiskZoneLocationResponse(boolean insideRiskZone, RiskZoneResponse riskZone) {
        this.insideRiskZone = insideRiskZone;
        this.riskZone = riskZone;
    }

    public boolean isInsideRiskZone() {
        return insideRiskZone;
    }

    public RiskZoneResponse getRiskZone() {
        return riskZone;
    }
}
