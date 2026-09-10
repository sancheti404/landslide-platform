package com.landslide.backend.service;

import com.landslide.backend.dto.DashboardStatisticsResponse;
import com.landslide.backend.entity.InfrastructureType;
import com.landslide.backend.entity.RiskLevel;
import com.landslide.backend.repository.InfrastructureRepository;
import com.landslide.backend.repository.LandslideEventRepository;
import com.landslide.backend.repository.RiskZoneRepository;
import org.springframework.stereotype.Service;

import java.util.EnumMap;
import java.util.HashMap;
import java.util.Map;

@Service
public class DashboardService {

    private final LandslideEventRepository landslideEventRepository;
    private final RiskZoneRepository riskZoneRepository;
    private final InfrastructureRepository infrastructureRepository;

    public DashboardService(
            LandslideEventRepository landslideEventRepository,
            RiskZoneRepository riskZoneRepository,
            InfrastructureRepository infrastructureRepository
    ) {
        this.landslideEventRepository = landslideEventRepository;
        this.riskZoneRepository = riskZoneRepository;
        this.infrastructureRepository = infrastructureRepository;
    }

    public DashboardStatisticsResponse getDashboardStatistics() {
        long totalLandslides = landslideEventRepository.count();

        Map<String, Long> landslidesBySeverity = new HashMap<>();
        for (Object[] result : landslideEventRepository.countLandslidesBySeverity()) {
            String severity = (String) result[0];
            Long count = (Long) result[1];
            if (severity != null) {
                landslidesBySeverity.put(severity, count);
            }
        }

        Map<String, Long> landslidesByStatus = new HashMap<>();
        for (Object[] result : landslideEventRepository.countLandslidesByStatus()) {
            String status = (String) result[0];
            Long count = (Long) result[1];
            if (status != null) {
                landslidesByStatus.put(status, count);
            }
        }

        Map<RiskLevel, Long> landslidesByRiskLevel = new EnumMap<>(RiskLevel.class);
        for (Object[] result : landslideEventRepository.countLandslidesByRiskLevel()) {
            RiskLevel riskLevel = (RiskLevel) result[0];
            Long count = (Long) result[1];
            if (riskLevel != null) {
                landslidesByRiskLevel.put(riskLevel, count);
            }
        }

        long unassignedLandslides = landslideEventRepository.countUnassignedLandslides();

        long totalRiskZones = riskZoneRepository.count();

        Map<RiskLevel, Long> riskZonesByRiskLevel = new EnumMap<>(RiskLevel.class);
        for (Object[] result : riskZoneRepository.countRiskZonesByRiskLevel()) {
            RiskLevel riskLevel = (RiskLevel) result[0];
            Long count = (Long) result[1];
            if (riskLevel != null) {
                riskZonesByRiskLevel.put(riskLevel, count);
            }
        }

        long totalInfrastructure = infrastructureRepository.count();

        Map<InfrastructureType, Long> infrastructureByType = new EnumMap<>(InfrastructureType.class);
        for (Object[] result : infrastructureRepository.countInfrastructureByType()) {
            InfrastructureType type = (InfrastructureType) result[0];
            Long count = (Long) result[1];
            if (type != null) {
                infrastructureByType.put(type, count);
            }
        }

        return new DashboardStatisticsResponse(
                totalLandslides,
                landslidesBySeverity,
                landslidesByStatus,
                landslidesByRiskLevel,
                unassignedLandslides,
                totalRiskZones,
                riskZonesByRiskLevel,
                totalInfrastructure,
                infrastructureByType
        );
    }
}
