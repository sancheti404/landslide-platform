package com.landslide.backend.service;

import com.landslide.backend.dto.CreateLandslideEventRequest;
import com.landslide.backend.dto.LandslideEventResponse;
import com.landslide.backend.entity.LandslideEvent;
import com.landslide.backend.entity.RiskLevel;
import com.landslide.backend.entity.RiskZone;
import com.landslide.backend.exception.ResourceNotFoundException;
import com.landslide.backend.repository.LandslideEventRepository;
import com.landslide.backend.repository.RiskZoneRepository;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.springframework.stereotype.Service;

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
                riskLevel
        );
    }
}
