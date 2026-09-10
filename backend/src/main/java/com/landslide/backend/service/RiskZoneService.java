package com.landslide.backend.service;

import com.landslide.backend.dto.CreateRiskZoneRequest;
import com.landslide.backend.dto.RiskZoneResponse;
import com.landslide.backend.entity.RiskZone;
import com.landslide.backend.exception.ResourceNotFoundException;
import com.landslide.backend.repository.RiskZoneRepository;

import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.io.WKTReader;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class RiskZoneService {

    private final RiskZoneRepository riskZoneRepository;

    public RiskZoneService(RiskZoneRepository riskZoneRepository) {
        this.riskZoneRepository = riskZoneRepository;
    }

    public RiskZoneResponse createRiskZone(
            CreateRiskZoneRequest request
    ) {

        try {
            WKTReader reader = new WKTReader();

            Geometry geometry = reader.read(request.getBoundary());

            if (!(geometry instanceof MultiPolygon)) {
                throw new IllegalArgumentException(
                        "Boundary must be a MULTIPOLYGON"
                );
            }

            MultiPolygon multiPolygon =
                    (MultiPolygon) geometry;

            multiPolygon.setSRID(4326);

            RiskZone riskZone = new RiskZone();

            riskZone.setName(request.getName());
            riskZone.setRiskLevel(request.getRiskLevel());
            riskZone.setBoundary(multiPolygon);
            riskZone.setDescription(request.getDescription());

            RiskZone savedRiskZone =
                    riskZoneRepository.save(riskZone);

            return mapToResponse(savedRiskZone);

        } catch (Exception exception) {

            throw new IllegalArgumentException(
                    "Invalid risk zone boundary: "
                            + exception.getMessage()
            );
        }
    }

    public List<RiskZoneResponse> getAllRiskZones() {

        return riskZoneRepository
                .findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    public RiskZoneResponse getRiskZoneById(Long id) {

        RiskZone riskZone =
                riskZoneRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Risk zone not found with id: " + id
                                )
                        );

        return mapToResponse(riskZone);
    }

    public List<RiskZoneResponse> findRiskZonesContainingPoint(
            Double latitude,
            Double longitude
    ) {
        return riskZoneRepository
                .findRiskZonesContainingPoint(latitude, longitude)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    private RiskZoneResponse mapToResponse(
            RiskZone riskZone
    ) {

        String boundaryWkt =
                riskZone.getBoundary().toText();

        return new RiskZoneResponse(
                riskZone.getId(),
                riskZone.getName(),
                riskZone.getRiskLevel(),
                boundaryWkt,
                riskZone.getDescription(),
                riskZone.getCreatedAt()
        );
    }
}
