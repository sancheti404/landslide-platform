package com.landslide.backend.service;

import com.landslide.backend.dto.CreateInfrastructureRequest;
import com.landslide.backend.dto.InfrastructureResponse;
import com.landslide.backend.entity.Infrastructure;
import com.landslide.backend.entity.InfrastructureType;
import com.landslide.backend.exception.ResourceNotFoundException;
import com.landslide.backend.repository.InfrastructureRepository;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class InfrastructureService {

    private final InfrastructureRepository infrastructureRepository;
    private final GeometryFactory geometryFactory = new GeometryFactory();

    public InfrastructureService(InfrastructureRepository infrastructureRepository) {
        this.infrastructureRepository = infrastructureRepository;
    }

    public InfrastructureResponse createInfrastructure(CreateInfrastructureRequest request) {
        Infrastructure infrastructure = new Infrastructure();

        infrastructure.setName(request.getName());
        infrastructure.setType(request.getType());
        infrastructure.setLatitude(request.getLatitude());
        infrastructure.setLongitude(request.getLongitude());
        infrastructure.setDescription(request.getDescription());

        Point location = geometryFactory.createPoint(
                new Coordinate(
                        request.getLongitude(),
                        request.getLatitude()
                )
        );
        location.setSRID(4326);
        infrastructure.setLocation(location);

        Infrastructure saved = infrastructureRepository.save(infrastructure);
        return mapToResponse(saved);
    }

    public List<InfrastructureResponse> getAllInfrastructure() {
        return infrastructureRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    public InfrastructureResponse getInfrastructureById(Long id) {
        Infrastructure infrastructure = infrastructureRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException(
                        "Infrastructure not found with id: " + id
                ));
        return mapToResponse(infrastructure);
    }

    public List<InfrastructureResponse> getInfrastructureByType(InfrastructureType type) {
        return infrastructureRepository.findByType(type)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    public List<InfrastructureResponse> findNearbyInfrastructure(
            Double latitude,
            Double longitude,
            Double distanceInKm
    ) {
        // Approximate 1 degree ~ 111 km for spatial bounding check
        Double distanceInDegrees = distanceInKm / 111.0;
        return infrastructureRepository.findInfrastructureNearPoint(latitude, longitude, distanceInDegrees)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    public void deleteInfrastructure(Long id) {
        if (!infrastructureRepository.existsById(id)) {
            throw new ResourceNotFoundException(
                    "Infrastructure not found with id: " + id
            );
        }
        infrastructureRepository.deleteById(id);
    }

    private InfrastructureResponse mapToResponse(Infrastructure infrastructure) {
        return new InfrastructureResponse(
                infrastructure.getId(),
                infrastructure.getName(),
                infrastructure.getType(),
                infrastructure.getLatitude(),
                infrastructure.getLongitude(),
                infrastructure.getDescription(),
                infrastructure.getCreatedAt()
        );
    }
}
