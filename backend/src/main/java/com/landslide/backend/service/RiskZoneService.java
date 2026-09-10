package com.landslide.backend.service;

import com.landslide.backend.dto.CreateRiskZoneRequest;
import com.landslide.backend.dto.RiskZoneLocationResponse;
import com.landslide.backend.dto.RiskZoneResponse;
import com.landslide.backend.dto.UpdateRiskZoneRequest;
import com.landslide.backend.entity.RiskZone;
import com.landslide.backend.exception.ResourceNotFoundException;
import com.landslide.backend.repository.LandslideEventRepository;
import com.landslide.backend.repository.RiskZoneRepository;

import org.locationtech.jts.geom.Geometry;
import org.locationtech.jts.geom.MultiPolygon;
import org.locationtech.jts.io.WKTReader;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class RiskZoneService {

    private final RiskZoneRepository riskZoneRepository;
    private final LandslideEventRepository landslideEventRepository;

    public RiskZoneService(
            RiskZoneRepository riskZoneRepository,
            LandslideEventRepository landslideEventRepository
    ) {
        this.riskZoneRepository = riskZoneRepository;
        this.landslideEventRepository = landslideEventRepository;
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

            if (riskZoneRepository.existsOverlappingRiskZone(request.getBoundary())) {
                throw new IllegalArgumentException(
                        "Risk zone boundary overlaps an existing risk zone"
                );
            }

            MultiPolygon multiPolygon = (MultiPolygon) geometry;
            multiPolygon.setSRID(4326);

            RiskZone riskZone = new RiskZone();
            riskZone.setName(request.getName());
            riskZone.setRiskLevel(request.getRiskLevel());
            riskZone.setBoundary(multiPolygon);
            riskZone.setDescription(request.getDescription());

            RiskZone savedRiskZone = riskZoneRepository.save(riskZone);
            return mapToResponse(savedRiskZone);

        } catch (IllegalArgumentException ex) {
            throw ex;
        } catch (Exception exception) {
            throw new IllegalArgumentException(
                    "Invalid risk zone boundary: " + exception.getMessage()
            );
        }
    }

    public RiskZoneResponse updateRiskZone(
            Long id,
            UpdateRiskZoneRequest request
    ) {
        RiskZone riskZone = riskZoneRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Risk zone not found with id: " + id
                ));

        try {
            WKTReader reader = new WKTReader();
            Geometry geometry = reader.read(request.getBoundary());

            if (!(geometry instanceof MultiPolygon)) {
                throw new IllegalArgumentException(
                        "Boundary must be a MULTIPOLYGON"
                );
            }

            if (riskZoneRepository.existsOverlappingRiskZoneExcludingId(request.getBoundary(), id)) {
                throw new IllegalArgumentException(
                        "Risk zone boundary overlaps an existing risk zone"
                );
            }

            MultiPolygon multiPolygon = (MultiPolygon) geometry;
            multiPolygon.setSRID(4326);

            riskZone.setName(request.getName());
            riskZone.setRiskLevel(request.getRiskLevel());
            riskZone.setBoundary(multiPolygon);
            riskZone.setDescription(request.getDescription());

            RiskZone updatedRiskZone = riskZoneRepository.save(riskZone);
            return mapToResponse(updatedRiskZone);

        } catch (IllegalArgumentException ex) {
            throw ex;
        } catch (Exception exception) {
            throw new IllegalArgumentException(
                    "Invalid risk zone boundary: " + exception.getMessage()
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
        RiskZone riskZone = riskZoneRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Risk zone not found with id: " + id
                ));
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

    public RiskZoneLocationResponse locatePoint(Double latitude, Double longitude) {
        List<RiskZone> matchingZones = riskZoneRepository.findRiskZonesContainingPoint(latitude, longitude);
        if (!matchingZones.isEmpty()) {
            return new RiskZoneLocationResponse(true, mapToResponse(matchingZones.get(0)));
        } else {
            return new RiskZoneLocationResponse(false, null);
        }
    }

    @Transactional
    public void deleteRiskZone(Long id) {
        RiskZone riskZone = riskZoneRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Risk zone not found with id: " + id
                ));

        landslideEventRepository.detachRiskZoneFromLandslides(id);
        riskZoneRepository.delete(riskZone);
    }

    private RiskZoneResponse mapToResponse(
            RiskZone riskZone
    ) {
        String boundaryWkt = riskZone.getBoundary().toText();

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
