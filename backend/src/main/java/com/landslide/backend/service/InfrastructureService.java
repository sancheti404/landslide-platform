package com.landslide.backend.service;

import com.landslide.backend.dto.CreateInfrastructureRequest;
import com.landslide.backend.dto.InfrastructureResponse;
import com.landslide.backend.entity.Infrastructure;
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

    private final GeometryFactory geometryFactory =
            new GeometryFactory();

    public InfrastructureService(
            InfrastructureRepository infrastructureRepository
    ) {
        this.infrastructureRepository = infrastructureRepository;
    }

    public InfrastructureResponse createInfrastructure(
            CreateInfrastructureRequest request
    ) {

        Infrastructure infrastructure =
                new Infrastructure();

        infrastructure.setName(request.getName());
        infrastructure.setType(request.getType());
        infrastructure.setLatitude(request.getLatitude());
        infrastructure.setLongitude(request.getLongitude());
        infrastructure.setDescription(request.getDescription());

        // IMPORTANT: X = longitude, Y = latitude
        Point location = geometryFactory.createPoint(
                new Coordinate(
                        request.getLongitude(),
                        request.getLatitude()
                )
        );

        location.setSRID(4326);

        infrastructure.setLocation(location);

        Infrastructure savedInfrastructure =
                infrastructureRepository.save(infrastructure);

        return mapToResponse(savedInfrastructure);
    }

    public List<InfrastructureResponse> getAllInfrastructure() {

        return infrastructureRepository
                .findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    public InfrastructureResponse getInfrastructureById(
            Long id
    ) {

        Infrastructure infrastructure =
                infrastructureRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Infrastructure not found with id: " + id
                                )
                        );

        return mapToResponse(infrastructure);
    }

    public List<InfrastructureResponse> findNearbyInfrastructure(
            Double latitude,
            Double longitude,
            Double distance
    ) {
        return infrastructureRepository
                .findNearbyInfrastructure(latitude, longitude, distance)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    public void deleteInfrastructure(Long id) {

        Infrastructure infrastructure =
                infrastructureRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Infrastructure not found with id: " + id
                                )
                        );

        infrastructureRepository.delete(infrastructure);
    }

    private InfrastructureResponse mapToResponse(
            Infrastructure infrastructure
    ) {

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
