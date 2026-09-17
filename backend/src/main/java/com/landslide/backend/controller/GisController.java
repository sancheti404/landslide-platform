package com.landslide.backend.controller;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.landslide.backend.dto.LandslideEventResponse;
import com.landslide.backend.service.LandslideEventService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/gis")
@Tag(name = "GIS & Boundary Services", description = "Authoritative and historical GIS data endpoints including state boundaries, GSI landslide inventory, and layer metadata")
public class GisController {

    private static final Logger log = LoggerFactory.getLogger(GisController.class);

    private final LandslideEventService landslideEventService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    private String cachedUttarakhandGeoJson = null;

    public GisController(LandslideEventService landslideEventService) {
        this.landslideEventService = landslideEventService;
    }

    @PostConstruct
    public void initBoundaryCache() {
        loadUttarakhandBoundary();
    }

    private synchronized void loadUttarakhandBoundary() {
        if (cachedUttarakhandGeoJson != null) {
            return;
        }

        // Search common paths relative to repo or backend
        Path[] candidatePaths = new Path[]{
                Paths.get("..", "ml", "data", "external", "geoBoundaries_IND_ADM1", "geoBoundaries-IND-ADM1_simplified.geojson"),
                Paths.get("ml", "data", "external", "geoBoundaries_IND_ADM1", "geoBoundaries-IND-ADM1_simplified.geojson"),
                Paths.get("C:", "Users", "hp", "OneDrive", "Desktop", "Landslide", "landslide-platform", "ml", "data", "external", "geoBoundaries_IND_ADM1", "geoBoundaries-IND-ADM1_simplified.geojson")
        };

        File geoJsonFile = null;
        for (Path p : candidatePaths) {
            File f = p.toFile();
            if (f.exists() && f.isFile()) {
                geoJsonFile = f;
                break;
            }
        }

        if (geoJsonFile == null) {
            log.warn("geoBoundaries file not found at any candidate path. State boundary endpoint will return fallback message.");
            return;
        }

        try {
            log.info("Loading Uttarakhand boundary from {}", geoJsonFile.getAbsolutePath());
            JsonNode root = objectMapper.readTree(geoJsonFile);
            JsonNode features = root.get("features");

            JsonNode uttarakhandFeature = null;
            if (features != null && features.isArray()) {
                for (JsonNode feat : features) {
                    JsonNode props = feat.get("properties");
                    if (props != null) {
                        String shapeName = props.has("shapeName") ? props.get("shapeName").asText() : "";
                        String shapeIso = props.has("shapeISO") ? props.get("shapeISO").asText() : "";
                        if ("Uttarakhand".equalsIgnoreCase(shapeName) || "IN-UT".equalsIgnoreCase(shapeIso)) {
                            uttarakhandFeature = feat;
                            break;
                        }
                    }
                }
            }

            if (uttarakhandFeature != null) {
                ObjectNode responseCollection = objectMapper.createObjectNode();
                responseCollection.put("type", "FeatureCollection");

                ObjectNode provenance = objectMapper.createObjectNode();
                provenance.put("dataset", "geoBoundaries ADM1 (India)");
                provenance.put("source", "William & Mary geoBoundaries (gbOpen)");
                provenance.put("state", "Uttarakhand");
                provenance.put("iso_code", "IN-UT");
                provenance.put("license", "Open Data Commons Open Database License (ODbL) / CC-BY 4.0");
                provenance.put("disclaimer", "External academic research boundary dataset. Not an official government or Survey of India boundary.");
                responseCollection.set("provenance", provenance);

                ArrayNode featureList = objectMapper.createArrayNode();
                featureList.add(uttarakhandFeature);
                responseCollection.set("features", featureList);

                this.cachedUttarakhandGeoJson = objectMapper.writeValueAsString(responseCollection);
                log.info("Successfully extracted and cached Uttarakhand state boundary GeoJSON ({} bytes)", cachedUttarakhandGeoJson.length());
            } else {
                log.warn("Uttarakhand feature ('shapeName': 'Uttarakhand' or 'shapeISO': 'IN-UT') not found in geoBoundaries file.");
            }
        } catch (Exception e) {
            log.error("Failed to parse geoBoundaries GeoJSON file: {}", e.getMessage(), e);
        }
    }

    @GetMapping(value = "/state-boundary", produces = MediaType.APPLICATION_JSON_VALUE)
    @Operation(
            summary = "Get Uttarakhand State Boundary GeoJSON",
            description = "Returns the Uttarakhand ADM1 state boundary polygon sourced from the William & Mary geoBoundaries gbOpen academic dataset. Preserves true external dataset provenance."
    )
    public ResponseEntity<String> getStateBoundary() {
        if (cachedUttarakhandGeoJson == null) {
            loadUttarakhandBoundary();
        }

        if (cachedUttarakhandGeoJson == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body("{\"error\": \"Uttarakhand state boundary GeoJSON is currently unavailable.\"}");
        }

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .body(cachedUttarakhandGeoJson);
    }

    @GetMapping("/historical-landslides")
    @Operation(
            summary = "Query GSI Historical Landslides",
            description = "Retrieves historical landslide events from the Geological Survey of India (GSI) National Landslide Susceptibility Mapping (NLSM) inventory. Supports filtering by district, movement type, and geographic bounding box."
    )
    public List<LandslideEventResponse> getHistoricalLandslides(
            @Parameter(description = "Filter by administrative district (e.g. Chamoli, Rudraprayag, Uttarkashi, Pithoragarh, Nainital, Tehri Garhwal)")
            @RequestParam(required = false) String district,

            @Parameter(description = "Filter by movement type (e.g. Debris Slide, Rock Fall, Rotational Slide, Flow)")
            @RequestParam(required = false) String movementType,

            @Parameter(description = "Minimum longitude of bounding box (e.g. 77.5)")
            @RequestParam(required = false) Double minLon,

            @Parameter(description = "Minimum latitude of bounding box (e.g. 28.5)")
            @RequestParam(required = false) Double minLat,

            @Parameter(description = "Maximum longitude of bounding box (e.g. 81.2)")
            @RequestParam(required = false) Double maxLon,

            @Parameter(description = "Maximum latitude of bounding box (e.g. 31.5)")
            @RequestParam(required = false) Double maxLat,

            @Parameter(description = "Maximum number of records to return (default 1000, max 6000)")
            @RequestParam(required = false, defaultValue = "1000") Integer limit
    ) {
        return landslideEventService.findHistoricalLandslides(district, movementType, minLon, minLat, maxLon, maxLat, limit);
    }

    @GetMapping("/district-summary")
    @Operation(
            summary = "GSI Landslides District Summary",
            description = "Returns the historical landslide counts per district in Uttarakhand from the GSI NLSM inventory."
    )
    public Map<String, Long> getDistrictSummary() {
        return landslideEventService.getDistrictSummary();
    }

    @GetMapping("/metadata")
    @Operation(
            summary = "GIS Data Catalog & Provenance Metadata",
            description = "Returns comprehensive metadata and provenance attribution for all GIS layers integrated in the platform."
    )
    public Map<String, Object> getGisMetadata() {
        Map<String, Object> metadata = new LinkedHashMap<>();

        metadata.put("operational_envelope", Map.of(
                "min_latitude", 28.5,
                "max_latitude", 31.6,
                "min_longitude", 77.4,
                "max_longitude", 81.3,
                "crs", "EPSG:4326 (WGS84)"
        ));

        metadata.put("layers", List.of(
                Map.of(
                        "name", "Uttarakhand State Boundary",
                        "type", "Vector Polygon (GeoJSON)",
                        "source", "William & Mary geoBoundaries (gbOpen)",
                        "level", "ADM1",
                        "license", "Open Data Commons Open Database License (ODbL) / CC-BY 4.0",
                        "status", "Reused existing local external dataset",
                        "notice", "Academic research boundary dataset. Not an official Survey of India boundary."
                ),
                Map.of(
                        "name", "Historical Landslide Inventory",
                        "type", "Vector Points",
                        "source", "Geological Survey of India (GSI) NLSM",
                        "count", 5523,
                        "attributes", List.of("slide_no", "district", "slide_name", "material_involved", "movement_type", "history"),
                        "status", "Authoritative GSI inventory normalized into PostGIS"
                ),
                Map.of(
                        "name", "Digital Elevation Model (DEM)",
                        "type", "Raster (GeoTIFF)",
                        "resolution", "30 meters",
                        "source", "SRTM GL1 30m DEM (NASA/USGS)",
                        "crs", "EPSG:4326 (WGS84)",
                        "status", "Reused existing local processed DEM"
                ),
                Map.of(
                        "name", "Precipitation Engine",
                        "type", "Daily Gridded Precipitation",
                        "resolution", "0.05 degree (~5.5 km)",
                        "source", "UCSB CHIRPS v2.0",
                        "status", "Reused existing offline cached grid"
                ),
                Map.of(
                        "name", "Risk Zones & Demo Infrastructure",
                        "type", "Vector Polygons & Points",
                        "source", "Synthetic / Demonstration PostGIS seed data",
                        "purpose", "Retained for spatial proximity query testing and local zone assignment"
                )
        ));

        return metadata;
    }
}
