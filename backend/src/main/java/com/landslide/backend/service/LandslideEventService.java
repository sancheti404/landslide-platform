package com.landslide.backend.service;

import com.landslide.backend.dto.CreateLandslideEventRequest;
import com.landslide.backend.dto.LandslideEventResponse;
import com.landslide.backend.entity.LandslideEvent;
import com.landslide.backend.exception.ResourceNotFoundException;
import com.landslide.backend.repository.LandslideEventRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class LandslideEventService {

    private final LandslideEventRepository landslideEventRepository;

    public LandslideEventService(
            LandslideEventRepository landslideEventRepository
    ) {
        this.landslideEventRepository = landslideEventRepository;
    }

    public LandslideEventResponse createEvent(
            CreateLandslideEventRequest request
    ) {
        LandslideEvent event = new LandslideEvent();

        event.setLatitude(request.getLatitude());
        event.setLongitude(request.getLongitude());
        event.setSeverity(request.getSeverity());
        event.setStatus(request.getStatus());
        event.setSource(request.getSource());
        event.setOccurredAt(request.getOccurredAt());

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
        return new LandslideEventResponse(
                event.getId(),
                event.getLatitude(),
                event.getLongitude(),
                event.getSeverity(),
                event.getStatus(),
                event.getSource(),
                event.getOccurredAt(),
                event.getCreatedAt()
        );
    }
}
