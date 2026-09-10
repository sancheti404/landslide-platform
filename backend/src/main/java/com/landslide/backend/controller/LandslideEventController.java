package com.landslide.backend.controller;

import com.landslide.backend.dto.CreateLandslideEventRequest;
import com.landslide.backend.dto.LandslideEventResponse;
import com.landslide.backend.service.LandslideEventService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/landslides")
public class LandslideEventController {

    private final LandslideEventService landslideEventService;

    public LandslideEventController(
            LandslideEventService landslideEventService
    ) {
        this.landslideEventService = landslideEventService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public LandslideEventResponse createEvent(
            @Valid @RequestBody CreateLandslideEventRequest request
    ) {
        return landslideEventService.createEvent(request);
    }

    @GetMapping
    public List<LandslideEventResponse> getAllEvents() {
        return landslideEventService.getAllEvents();
    }

    @GetMapping("/{id}")
    public LandslideEventResponse getEventById(
            @PathVariable Long id
    ) {
        return landslideEventService.getEventById(id);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteEvent(
            @PathVariable Long id
    ) {
        landslideEventService.deleteEvent(id);
    }
}
