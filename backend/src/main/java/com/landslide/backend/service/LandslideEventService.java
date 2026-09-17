package com.landslide.backend.service;

import com.landslide.backend.dto.CreateLandslideEventRequest;
import com.landslide.backend.dto.LandslideEventResponse;
import com.landslide.backend.entity.LandslideEvent;
import com.landslide.backend.entity.RiskLevel;
import com.landslide.backend.entity.RiskZone;
import com.landslide.backend.exception.ResourceNotFoundException;
import com.landslide.backend.repository.LandslideEventRepository;
import com.landslide.backend.repository.RiskZoneRepository;
import jakarta.persistence.criteria.Predicate;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Service
public class LandslideEventService {

    private final LandslideEventRepository landslideEventRepository;
    private final RiskZoneRepository riskZoneRepository;
    private final GeometryFactory geometryFactory = new GeometryFactory();

    public LandslideEventService(
            LandslideEventRepository landslideEventRepository,
            RiskZoneRepository riskZoneRepository
    ) {
        this.landslideEventRepository = landslideEventRepository;
        this.riskZoneRepository = riskZoneRepository;
    }

    public LandslideEventResponse createEvent(
            CreateLandslideEventRequest request
    ) {
        LandslideEvent event = new LandslideEvent();

        event.setLatitude(request.getLatitude());
        event.setLongitude(request.getLongitude());

        Point location = geometryFactory.createPoint(
                new Coordinate(
                        request.getLongitude(),
                        request.getLatitude()
                )
        );
        location.setSRID(4326);
        event.setLocation(location);

        event.setSeverity(request.getSeverity());
        event.setStatus(request.getStatus());
        event.setSource(request.getSource());
        event.setOccurredAt(request.getOccurredAt());

        List<RiskZone> matchingZones =
                riskZoneRepository.findRiskZonesContainingPoint(
                        request.getLatitude(),
                        request.getLongitude()
                );

        if (!matchingZones.isEmpty()) {
            event.setRiskZone(matchingZones.get(0));
        }

        LandslideEvent savedEvent =
                landslideEventRepository.save(event);

        return mapToResponse(savedEvent);
    }

    public List<LandslideEventResponse> getAllEvents() {
        return landslideEventRepository
                .findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    public List<LandslideEventResponse> filterEvents(
            String severity,
            String status,
            RiskLevel riskLevel,
            Long riskZoneId,
            LocalDateTime occurredFrom,
            LocalDateTime occurredTo
    ) {
        if (occurredFrom != null && occurredTo != null && occurredFrom.isAfter(occurredTo)) {
            throw new IllegalArgumentException("occurredFrom cannot be after occurredTo");
        }

        Specification<LandslideEvent> spec = (root, query, criteriaBuilder) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (severity != null && !severity.isBlank()) {
                predicates.add(criteriaBuilder.equal(root.get("severity"), severity));
            }

            if (status != null && !status.isBlank()) {
                predicates.add(criteriaBuilder.equal(root.get("status"), status));
            }

            if (riskLevel != null) {
                predicates.add(criteriaBuilder.equal(root.get("riskZone").get("riskLevel"), riskLevel));
            }

            if (riskZoneId != null) {
                predicates.add(criteriaBuilder.equal(root.get("riskZone").get("id"), riskZoneId));
            }

            if (occurredFrom != null) {
                predicates.add(criteriaBuilder.greaterThanOrEqualTo(root.get("occurredAt"), occurredFrom));
            }

            if (occurredTo != null) {
                predicates.add(criteriaBuilder.lessThanOrEqualTo(root.get("occurredAt"), occurredTo));
            }

            return criteriaBuilder.and(predicates.toArray(new Predicate[0]));
        };

        return landslideEventRepository.findAll(spec)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    public List<LandslideEventResponse> findNearbyLandslides(
            Double latitude,
            Double longitude,
            Double distance
    ) {
        if (latitude == null || latitude < -90.0 || latitude > 90.0) {
            throw new IllegalArgumentException("Latitude must be between -90 and 90");
        }
        if (longitude == null || longitude < -180.0 || longitude > 180.0) {
            throw new IllegalArgumentException("Longitude must be between -180 and 180");
        }
        if (distance == null || distance <= 0) {
            throw new IllegalArgumentException("Distance must be greater than 0");
        }

        return landslideEventRepository.findNearbyLandslides(latitude, longitude, distance)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    public LandslideEventResponse getEventById(Long id) {

        LandslideEvent event =
                landslideEventRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Landslide event not found with id: " + id
                                )
                        );

        return mapToResponse(event);
    }

    public void deleteEvent(Long id) {

        if (!landslideEventRepository.existsById(id)) {
            throw new ResourceNotFoundException(
                    "Landslide event not found with id: " + id
            );
        }

        landslideEventRepository.deleteById(id);
    }

    public List<LandslideEventResponse> findHistoricalLandslides(
            String district,
            String movementType,
            Double minLon,
            Double minLat,
            Double maxLon,
            Double maxLat,
            Integer limit
    ) {
        int maxResults = (limit != null && limit > 0 && limit <= 10000) ? limit : 1000;
        List<LandslideEvent> events;

        if (minLon != null && minLat != null && maxLon != null && maxLat != null) {
            events = landslideEventRepository.findLandslidesInBoundingBox(minLon, minLat, maxLon, maxLat, maxResults);
        } else if (district != null && !district.isBlank()) {
            events = landslideEventRepository.findBySourceAndDistrict("GSI_NLSM", district.trim());
        } else {
            events = landslideEventRepository.findBySource("GSI_NLSM");
        }

        if (movementType != null && !movementType.isBlank()) {
            String mtLower = movementType.trim().toLowerCase();
            events = events.stream()
                    .filter(e -> e.getMovementType() != null && e.getMovementType().toLowerCase().contains(mtLower))
                    .toList();
        }

        if (events.size() > maxResults) {
            events = events.subList(0, maxResults);
        }

        return events.stream().map(this::mapToResponse).toList();
    }

    public java.util.Map<String, Long> getDistrictSummary() {
        List<Object[]> rows = landslideEventRepository.countLandslidesByDistrict("GSI_NLSM");
        java.util.Map<String, Long> summary = new java.util.LinkedHashMap<>();
        for (Object[] r : rows) {
            if (r[0] != null && r[1] != null) {
                summary.put((String) r[0], ((Number) r[1]).longValue());
            }
        }
        return summary;
    }

    private LandslideEventResponse mapToResponse(
            LandslideEvent event
    ) {
        Long riskZoneId = null;
        String riskZoneName = null;
        RiskLevel riskLevel = null;

        if (event.getRiskZone() != null) {
            riskZoneId = event.getRiskZone().getId();
            riskZoneName = event.getRiskZone().getName();
            riskLevel = event.getRiskZone().getRiskLevel();
        }

        return new LandslideEventResponse(
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
                riskLevel,
                event.getSlideNo(),
                event.getDistrict(),
                event.getSlideName(),
                event.getMaterialInvolved(),
                event.getMovementType(),
                event.getHistory()
        );
    }
}

