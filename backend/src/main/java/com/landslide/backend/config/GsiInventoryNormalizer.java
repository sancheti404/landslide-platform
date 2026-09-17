package com.landslide.backend.config;

import com.landslide.backend.entity.LandslideEvent;
import com.landslide.backend.repository.LandslideEventRepository;
import org.locationtech.jts.geom.Coordinate;
import org.locationtech.jts.geom.GeometryFactory;
import org.locationtech.jts.geom.Point;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Normalizes authentic Geological Survey of India (GSI) historical landslide inventory
 * from ml/data/processed/uttarakhand_landslide_inventory_clean.csv into PostGIS.
 * Idempotent: executed once; skipped if GSI_NLSM records already exist.
 */
@Component
@Order(10)
public class GsiInventoryNormalizer implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(GsiInventoryNormalizer.class);
    private static final int BATCH_SIZE = 500;

    private final LandslideEventRepository landslideEventRepository;
    private final GeometryFactory geometryFactory = new GeometryFactory();

    public GsiInventoryNormalizer(LandslideEventRepository landslideEventRepository) {
        this.landslideEventRepository = landslideEventRepository;
    }

    @Override
    public void run(String... args) {
        long existingCount = landslideEventRepository.countBySource("GSI_NLSM");
        if (existingCount > 0) {
            log.info("GSI Historical Landslide Inventory already normalized in PostGIS ({} records found). Skipping normalization.", existingCount);
            return;
        }

        Path csvPath = resolveInventoryCsvPath();
        if (csvPath == null || !Files.exists(csvPath)) {
            log.warn("GSI inventory clean CSV not found at expected paths. Skipping normalization.");
            return;
        }

        log.info("Starting normalization of authentic GSI Landslide Inventory into PostGIS from {}", csvPath.toAbsolutePath());
        long t0 = System.currentTimeMillis();
        int totalIngested = 0;

        try (BufferedReader reader = Files.newBufferedReader(csvPath, StandardCharsets.UTF_8)) {
            String header = reader.readLine();
            if (header == null) {
                return;
            }

            List<LandslideEvent> batch = new ArrayList<>(BATCH_SIZE);
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.trim().isEmpty()) {
                    continue;
                }

                String[] cols = parseCsvLine(line);
                if (cols.length < 5) {
                    continue;
                }

                try {
                    String slideNo = cols[0].trim();
                    String district = cols[1].trim();
                    String slideName = cols.length > 2 ? cols[2].trim() : "";
                    double lat = Double.parseDouble(cols[3].trim());
                    double lon = Double.parseDouble(cols[4].trim());
                    String material = cols.length > 5 ? cols[5].trim() : "Unspecified";
                    String movement = cols.length > 6 ? cols[6].trim() : "Slide";
                    String history = cols.length > 7 ? cols[7].trim() : "";

                    LandslideEvent event = new LandslideEvent();
                    event.setLatitude(lat);
                    event.setLongitude(lon);

                    Point location = geometryFactory.createPoint(new Coordinate(lon, lat));
                    location.setSRID(4326);
                    event.setLocation(location);

                    event.setSlideNo(slideNo.isEmpty() ? null : slideNo);
                    event.setDistrict(district.isEmpty() ? null : district);
                    event.setSlideName(slideName.isEmpty() ? null : slideName);
                    event.setMaterialInvolved(material.isEmpty() ? null : material);
                    event.setMovementType(movement.isEmpty() ? null : movement);
                    event.setHistory(history.isEmpty() ? null : history);

                    event.setSeverity("HIGH");
                    event.setStatus("HISTORICAL");
                    event.setSource("GSI_NLSM");

                    LocalDateTime occurredAt = parseYearFromHistory(history);
                    event.setOccurredAt(occurredAt);

                    batch.add(event);

                    if (batch.size() >= BATCH_SIZE) {
                        landslideEventRepository.saveAll(batch);
                        totalIngested += batch.size();
                        batch.clear();
                    }
                } catch (Exception parseEx) {
                    log.debug("Skipping unparseable GSI inventory row: {}", line);
                }
            }

            if (!batch.isEmpty()) {
                landslideEventRepository.saveAll(batch);
                totalIngested += batch.size();
                batch.clear();
            }

            long elapsed = System.currentTimeMillis() - t0;
            log.info("Successfully normalized {} authentic GSI landslide records into PostGIS in {} ms.", totalIngested, elapsed);

        } catch (Exception e) {
            log.error("Error during GSI inventory normalization: {}", e.getMessage(), e);
        }
    }

    private Path resolveInventoryCsvPath() {
        Path[] candidates = new Path[]{
                Paths.get("../ml/data/processed/uttarakhand_landslide_inventory_clean.csv"),
                Paths.get("ml/data/processed/uttarakhand_landslide_inventory_clean.csv"),
                Paths.get("../../ml/data/processed/uttarakhand_landslide_inventory_clean.csv"),
                Paths.get("c:/Users/hp/OneDrive/Desktop/Landslide/landslide-platform/ml/data/processed/uttarakhand_landslide_inventory_clean.csv")
        };
        for (Path p : candidates) {
            if (Files.exists(p)) {
                return p;
            }
        }
        return null;
    }

    private String[] parseCsvLine(String line) {
        // Robust regex matching commas outside quotes
        return line.split(",(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", -1);
    }

    private LocalDateTime parseYearFromHistory(String history) {
        if (history == null || history.isBlank()) {
            return null;
        }
        try {
            // Find 4 consecutive digits for year (e.g. 2013, 2014)
            java.util.regex.Matcher m = java.util.regex.Pattern.compile("\\b(19\\d\\d|20\\d\\d)\\b").matcher(history);
            if (m.find()) {
                int year = Integer.parseInt(m.group(1));
                return LocalDateTime.of(year, 1, 1, 0, 0);
            }
        } catch (Exception ignored) {
        }
        return null;
    }
}
