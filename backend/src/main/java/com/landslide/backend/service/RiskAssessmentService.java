package com.landslide.backend.service;

import com.landslide.backend.dto.InfrastructureResponse;
import com.landslide.backend.dto.RiskAssessmentRequest;
import com.landslide.backend.dto.RiskAssessmentResponse;
import com.landslide.backend.entity.InfrastructureType;
import com.landslide.backend.entity.RiskZone;
import com.landslide.backend.repository.RiskZoneRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;

@Service
public class RiskAssessmentService {

    private static final Logger log = LoggerFactory.getLogger(RiskAssessmentService.class);
    private static final double DEFAULT_INFRASTRUCTURE_RADIUS_METERS = 5000.0;

    private final MlInferenceClient mlInferenceClient;
    private final RiskZoneRepository riskZoneRepository;
    private final InfrastructureService infrastructureService;
    private final com.landslide.backend.validation.UttarakhandGeoValidator geoValidator;

    public RiskAssessmentService(
            MlInferenceClient mlInferenceClient,
            RiskZoneRepository riskZoneRepository,
            InfrastructureService infrastructureService,
            com.landslide.backend.validation.UttarakhandGeoValidator geoValidator
    ) {
        this.mlInferenceClient = mlInferenceClient;
        this.riskZoneRepository = riskZoneRepository;
        this.infrastructureService = infrastructureService;
        this.geoValidator = geoValidator;
    }

    public RiskAssessmentResponse assessLandslideRisk(RiskAssessmentRequest request) {
        return assessLandslideRisk(request, java.util.UUID.randomUUID().toString());
    }

    public RiskAssessmentResponse assessLandslideRisk(RiskAssessmentRequest request, String requestId) {
        long t0 = System.currentTimeMillis();
        log.info("Processing operational landslide risk assessment [req_id={}] for ({}, {}) at {}",
                requestId, request.getLatitude(), request.getLongitude(), request.getTimestamp());

        // 0. Explicit Geographic Operational Envelope Validation
        geoValidator.validateOperationalEnvelope(request.getLatitude(), request.getLongitude());

        // 1. Invoke Python Multimodal ML Inference Service
        long tMlStart = System.currentTimeMillis();
        RiskAssessmentResponse response = mlInferenceClient.assessRisk(request, requestId);
        long mlDuration = System.currentTimeMillis() - tMlStart;

        // 2. PostGIS Spatial Query: Check intersecting mapped Risk Zones
        long tGisStart = System.currentTimeMillis();
        List<RiskZone> containingZones = riskZoneRepository.findRiskZonesContainingPoint(
                request.getLatitude(), request.getLongitude()
        );

        if (!containingZones.isEmpty()) {
            RiskZone matchedZone = containingZones.get(0);
            response.setIntersectingRiskZoneId(matchedZone.getId());
            response.setIntersectingRiskZoneName(matchedZone.getName());
            response.setIntersectingRiskZoneLevel(matchedZone.getRiskLevel());
            log.info("Location ({}, {}) falls inside PostGIS RiskZone: {} [ID: {}] [req_id={}]",
                    request.getLatitude(), request.getLongitude(), matchedZone.getName(), matchedZone.getId(), requestId);
        }

        // 3. PostGIS Spatial Query: Count nearby critical infrastructure within 5 km
        try {
            List<InfrastructureResponse> hospitals = infrastructureService.findNearbyInfrastructure(
                    request.getLatitude(), request.getLongitude(),
                    DEFAULT_INFRASTRUCTURE_RADIUS_METERS, InfrastructureType.HOSPITAL
            );
            List<InfrastructureResponse> shelters = infrastructureService.findNearbyInfrastructure(
                    request.getLatitude(), request.getLongitude(),
                    DEFAULT_INFRASTRUCTURE_RADIUS_METERS, InfrastructureType.SHELTER
            );
            List<InfrastructureResponse> police = infrastructureService.findNearbyInfrastructure(
                    request.getLatitude(), request.getLongitude(),
                    DEFAULT_INFRASTRUCTURE_RADIUS_METERS, InfrastructureType.POLICE_STATION
            );
            List<InfrastructureResponse> roads = infrastructureService.findNearbyInfrastructure(
                    request.getLatitude(), request.getLongitude(),
                    DEFAULT_INFRASTRUCTURE_RADIUS_METERS, InfrastructureType.ROAD
            );

            response.setNearbyHospitalsCount(hospitals.size());
            response.setNearbySheltersCount(shelters.size());
            response.setNearbyPoliceStationsCount(police.size());
            response.setNearbyRoadsCount(roads.size());
        } catch (Exception e) {
            log.warn("Failed to retrieve nearby infrastructure for ({}, {}) [req_id={}]: {}",
                    request.getLatitude(), request.getLongitude(), requestId, e.getMessage());
        }

        long gisDuration = System.currentTimeMillis() - tGisStart;
        long totalDuration = System.currentTimeMillis() - t0;

        log.info("Risk assessment complete [req_id={}] -> Score: {} [{}] in {} ms (ML: {} ms, PostGIS: {} ms)",
                requestId, response.getOperationalLandslideRiskScore(), response.getRiskLevel(),
                totalDuration, mlDuration, gisDuration);

        return response;
    }


    public Map<String, Object> checkMlHealth() {
        return mlInferenceClient.checkHealth();
    }
}
