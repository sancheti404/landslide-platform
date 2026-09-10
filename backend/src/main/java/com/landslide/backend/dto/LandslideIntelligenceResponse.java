package com.landslide.backend.dto;

public class LandslideIntelligenceResponse {

    private LandslideEventResponse landslide;
    private RiskZoneResponse riskZone;
    private NearbyInfrastructureResponse nearbyInfrastructure;

    public LandslideIntelligenceResponse(
            LandslideEventResponse landslide,
            RiskZoneResponse riskZone,
            NearbyInfrastructureResponse nearbyInfrastructure
    ) {
        this.landslide = landslide;
        this.riskZone = riskZone;
        this.nearbyInfrastructure = nearbyInfrastructure;
    }

    public LandslideEventResponse getLandslide() {
        return landslide;
    }

    public RiskZoneResponse getRiskZone() {
        return riskZone;
    }

    public NearbyInfrastructureResponse getNearbyInfrastructure() {
        return nearbyInfrastructure;
    }
}
