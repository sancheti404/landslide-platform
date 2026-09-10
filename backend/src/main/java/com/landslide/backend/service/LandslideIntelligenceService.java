package com.landslide.backend.service;

import com.landslide.backend.dto.InfrastructureResponse;
import com.landslide.backend.dto.LandslideEventResponse;
import com.landslide.backend.dto.LandslideIntelligenceResponse;
import com.landslide.backend.dto.NearbyInfrastructureResponse;
import com.landslide.backend.dto.RiskZoneResponse;
import com.landslide.backend.entity.InfrastructureType;
import com.landslide.backend.entity.LandslideEvent;
import com.landslide.backend.entity.RiskLevel;
import com.landslide.backend.exception.ResourceNotFoundException;
import com.landslide.backend.repository.LandslideEventRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class LandslideIntelligenceService {

    private static final double DEFAULT_NEARBY_DISTANCE_METERS = 5000.0;

    private final LandslideEventRepository landslideEventRepository;
    private final InfrastructureService infrastructureService;

    public LandslideIntelligenceService(
            LandslideEventRepository landslideEventRepository,
            InfrastructureService infrastructureService
    ) {
        this.landslideEventRepository = landslideEventRepository;
        this.infrastructureService = infrastructureService;
    }

    public LandslideIntelligenceResponse getLandslideIntelligence(Long id) {
        LandslideEvent event = landslideEventRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Landslide event not found with id: " + id
                ));

        Double latitude = event.getLatitude();
        Double longitude = event.getLongitude();

        // 1. Build RiskZoneResponse (if risk zone is assigned)
        Long riskZoneId = null;
        String riskZoneName = null;
        RiskLevel riskLevel = null;
        RiskZoneResponse riskZoneResponse = null;

        if (event.getRiskZone() != null) {
            riskZoneId = event.getRiskZone().getId();
            riskZoneName = event.getRiskZone().getName();
            riskLevel = event.getRiskZone().getRiskLevel();

            String boundaryWkt = event.getRiskZone().getBoundary() != null ? event.getRiskZone().getBoundary().toText() : null;
            riskZoneResponse = new RiskZoneResponse(
                    event.getRiskZone().getId(),
                    event.getRiskZone().getName(),
                    event.getRiskZone().getRiskLevel(),
                    boundaryWkt,
                    event.getRiskZone().getDescription(),
                    event.getRiskZone().getCreatedAt()
            );
        }

        // 2. Build LandslideEventResponse
        LandslideEventResponse landslideResponse = new LandslideEventResponse(
                event.getId(),
                event.getLatitude(),
                event.getLongitude(),
                event.getSeverity(),
                event.getStatus(),
                event.getSource(),
                event.getOccurredAt(),
                event.getCreatedAt(),
                riskZoneId,
                riskZoneName,
                riskLevel
        );

        // 3. Query nearby infrastructure by type (5000 meters)
        List<InfrastructureResponse> hospitals = infrastructureService.findNearbyInfrastructure(
                latitude, longitude, DEFAULT_NEARBY_DISTANCE_METERS, InfrastructureType.HOSPITAL
        );
        List<InfrastructureResponse> shelters = infrastructureService.findNearbyInfrastructure(
                latitude, longitude, DEFAULT_NEARBY_DISTANCE_METERS, InfrastructureType.SHELTER
        );
        List<InfrastructureResponse> policeStations = infrastructureService.findNearbyInfrastructure(
                latitude, longitude, DEFAULT_NEARBY_DISTANCE_METERS, InfrastructureType.POLICE_STATION
        );
        List<InfrastructureResponse> roads = infrastructureService.findNearbyInfrastructure(
                latitude, longitude, DEFAULT_NEARBY_DISTANCE_METERS, InfrastructureType.ROAD
        );

        NearbyInfrastructureResponse nearbyInfrastructure = new NearbyInfrastructureResponse(
                hospitals,
                shelters,
                policeStations,
                roads
        );

        return new LandslideIntelligenceResponse(
                landslideResponse,
                riskZoneResponse,
                nearbyInfrastructure
        );
    }
}
