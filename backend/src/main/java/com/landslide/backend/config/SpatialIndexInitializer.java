package com.landslide.backend.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

@Component
public class SpatialIndexInitializer implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(SpatialIndexInitializer.class);

    private final JdbcTemplate jdbcTemplate;

    public SpatialIndexInitializer(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public void run(String... args) {
        log.info("Initializing PostGIS GiST spatial indexes...");
        try {
            jdbcTemplate.execute("CREATE INDEX IF NOT EXISTS idx_risk_zones_boundary_gist ON risk_zones USING GIST (boundary);");
            jdbcTemplate.execute("CREATE INDEX IF NOT EXISTS idx_landslide_events_location_gist ON landslide_events USING GIST (location);");
            jdbcTemplate.execute("CREATE INDEX IF NOT EXISTS idx_infrastructure_location_gist ON infrastructure USING GIST (location);");
            log.info("PostGIS spatial GiST indexes created/verified successfully.");
        } catch (Exception e) {
            log.warn("Spatial index initialization warning: {}", e.getMessage());
        }
    }
}
