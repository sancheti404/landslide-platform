package com.landslide.backend.config;

import com.landslide.backend.dto.CreateInfrastructureRequest;
import com.landslide.backend.dto.CreateLandslideEventRequest;
import com.landslide.backend.dto.CreateRiskZoneRequest;
import com.landslide.backend.entity.InfrastructureType;
import com.landslide.backend.entity.RiskLevel;
import com.landslide.backend.repository.InfrastructureRepository;
import com.landslide.backend.repository.LandslideEventRepository;
import com.landslide.backend.repository.RiskZoneRepository;
import com.landslide.backend.service.InfrastructureService;
import com.landslide.backend.service.LandslideEventService;
import com.landslide.backend.service.RiskZoneService;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
@ConditionalOnProperty(name = "app.seed-data", havingValue = "true")
public class DataSeeder implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataSeeder.class);

    private final RiskZoneService riskZoneService;
    private final InfrastructureService infrastructureService;
    private final LandslideEventService landslideEventService;
    private final RiskZoneRepository riskZoneRepository;

    public DataSeeder(
            RiskZoneService riskZoneService,
            InfrastructureService infrastructureService,
            LandslideEventService landslideEventService,
            RiskZoneRepository riskZoneRepository
    ) {
        this.riskZoneService = riskZoneService;
        this.infrastructureService = infrastructureService;
        this.landslideEventService = landslideEventService;
        this.riskZoneRepository = riskZoneRepository;
    }

    @Override
    public void run(String... args) {
        log.info("Checking demo GIS dataset seeding condition...");

        // Idempotency check: if the sample risk zone already exists by name, skip seeding
        if (riskZoneRepository.findAll().stream().anyMatch(z -> "Dehradun High Risk Slopes".equals(z.getName()))) {
            log.info("Sample GIS dataset already seeded. Skipping sample data seeding to ensure idempotency.");
            return;
        }

        log.info("Seeding realistic sample GIS dataset for Landslide Platform...");

        // 1. Seed 3 Non-Overlapping Risk Zones
        seedRiskZone("Dehradun High Risk Slopes", RiskLevel.HIGH,
                "MULTIPOLYGON (((78.40 30.40, 78.45 30.40, 78.45 30.45, 78.40 30.45, 78.40 30.40)))",
                "High slope instability area around Dehradun hills");

        seedRiskZone("Mussoorie Medium Hazard Corridor", RiskLevel.MEDIUM,
                "MULTIPOLYGON (((78.46 30.46, 78.50 30.46, 78.50 30.50, 78.46 30.50, 78.46 30.46)))",
                "Medium risk highway corridor near Mussoorie");

        seedRiskZone("Rishikesh Valley Buffer", RiskLevel.LOW,
                "MULTIPOLYGON (((78.51 30.05, 78.55 30.05, 78.55 30.10, 78.51 30.10, 78.51 30.05)))",
                "Low risk river valley buffer area");

        // 2. Seed 10 Infrastructure Items across 6 Types
        seedInfrastructure("Max Super Speciality Hospital", InfrastructureType.HOSPITAL, 30.415, 78.415, "Primary trauma center near Dehradun");
        seedInfrastructure("Synergy Community Hospital", InfrastructureType.HOSPITAL, 30.470, 78.475, "Emergency clinic near Mussoorie");

        seedInfrastructure("Rajpur Community Relief Center", InfrastructureType.SHELTER, 30.420, 78.420, "Emergency disaster shelter");
        seedInfrastructure("Hillside Emergency Shelter", InfrastructureType.SHELTER, 30.480, 78.480, "High altitude evacuation shelter");

        seedInfrastructure("Rajpur Road Police Station", InfrastructureType.POLICE_STATION, 30.418, 78.418, "Central district police control post");
        seedInfrastructure("Mussoorie Town Outpost", InfrastructureType.POLICE_STATION, 30.475, 78.470, "Hill outpost police station");

        seedInfrastructure("Rajpur Road Bypass", InfrastructureType.ROAD, 30.422, 78.422, "Critical access highway");
        seedInfrastructure("Mussoorie Dehradun Expressway", InfrastructureType.ROAD, 30.465, 78.465, "Main arterial mountain road");

        seedInfrastructure("St. Joseph Academy", InfrastructureType.SCHOOL, 30.425, 78.425, "Educational institution & secondary shelter");
        seedInfrastructure("Song River Bridge", InfrastructureType.BRIDGE, 30.080, 78.520, "Valley river crossing bridge");

        // 3. Seed 10 Landslide Events (In-zone & Out-of-zone)
        // Inside Dehradun High Risk Slopes (HIGH)
        seedLandslide(30.412, 78.415, "HIGH", "ACTIVE", "SENSOR", LocalDateTime.now().minusDays(1));
        seedLandslide(30.430, 78.435, "CRITICAL", "ACTIVE", "FIELD_REPORT", LocalDateTime.now().minusHours(5));
        seedLandslide(30.440, 78.445, "MEDIUM", "RESOLVED", "SENSOR", LocalDateTime.now().minusDays(3));

        // Inside Mussoorie Medium Hazard Corridor (MEDIUM)
        seedLandslide(30.470, 78.470, "MEDIUM", "MONITORING", "SATELLITE", LocalDateTime.now().minusDays(2));
        seedLandslide(30.485, 78.485, "HIGH", "ACTIVE", "SENSOR", LocalDateTime.now().minusHours(12));
        seedLandslide(30.495, 78.490, "LOW", "RESOLVED", "FIELD_REPORT", LocalDateTime.now().minusDays(5));

        // Inside Rishikesh Valley Buffer (LOW)
        seedLandslide(30.060, 78.520, "LOW", "MONITORING", "SENSOR", LocalDateTime.now().minusDays(4));
        seedLandslide(30.080, 78.540, "LOW", "RESOLVED", "SENSOR", LocalDateTime.now().minusDays(7));

        // Outside ALL Risk Zones (riskZone = null)
        seedLandslide(30.900, 78.900, "MEDIUM", "MONITORING", "SATELLITE", LocalDateTime.now().minusDays(1));
        seedLandslide(15.000, 15.000, "LOW", "RESOLVED", "TEST", LocalDateTime.now().minusDays(10));

        log.info("Realistic sample GIS dataset seeded successfully!");
    }

    private void seedRiskZone(String name, RiskLevel level, String boundary, String desc) {
        try {
            CreateRiskZoneRequest req = new CreateRiskZoneRequest();
            req.setName(name);
            req.setRiskLevel(level);
            req.setBoundary(boundary);
            req.setDescription(desc);
            riskZoneService.createRiskZone(req);
        } catch (Exception e) {
            log.warn("Sample risk zone creation note: {}", e.getMessage());
        }
    }

    private void seedInfrastructure(String name, InfrastructureType type, double lat, double lon, String desc) {
        try {
            CreateInfrastructureRequest req = new CreateInfrastructureRequest();
            req.setName(name);
            req.setType(type);
            req.setLatitude(lat);
            req.setLongitude(lon);
            req.setDescription(desc);
            infrastructureService.createInfrastructure(req);
        } catch (Exception e) {
            log.warn("Sample infrastructure creation note: {}", e.getMessage());
        }
    }

    private void seedLandslide(double lat, double lon, String severity, String status, String source, LocalDateTime occurredAt) {
        try {
            CreateLandslideEventRequest req = new CreateLandslideEventRequest();
            req.setLatitude(lat);
            req.setLongitude(lon);
            req.setSeverity(severity);
            req.setStatus(status);
            req.setSource(source);
            req.setOccurredAt(occurredAt);
            landslideEventService.createEvent(req);
        } catch (Exception e) {
            log.warn("Sample landslide creation note: {}", e.getMessage());
        }
    }
}
