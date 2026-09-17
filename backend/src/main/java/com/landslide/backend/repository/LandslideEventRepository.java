package com.landslide.backend.repository;

import com.landslide.backend.entity.LandslideEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface LandslideEventRepository
        extends JpaRepository<LandslideEvent, Long>, JpaSpecificationExecutor<LandslideEvent> {

    @Modifying
    @Query("UPDATE LandslideEvent l SET l.riskZone = null WHERE l.riskZone.id = :riskZoneId")
    void detachRiskZoneFromLandslides(@Param("riskZoneId") Long riskZoneId);

    @Query(value = """
            SELECT *
            FROM landslide_events le
            WHERE ST_DWithin(
                le.location::geography,
                ST_SetSRID(
                    ST_MakePoint(:longitude, :latitude),
                    4326
                )::geography,
                :distance
            )
            """, nativeQuery = true)
    List<LandslideEvent> findNearbyLandslides(
            @Param("latitude") Double latitude,
            @Param("longitude") Double longitude,
            @Param("distance") Double distance
    );

    @Query("SELECT l.severity, COUNT(l) FROM LandslideEvent l GROUP BY l.severity")
    List<Object[]> countLandslidesBySeverity();

    @Query("SELECT l.status, COUNT(l) FROM LandslideEvent l GROUP BY l.status")
    List<Object[]> countLandslidesByStatus();

    @Query("SELECT r.riskLevel, COUNT(l) FROM LandslideEvent l JOIN l.riskZone r GROUP BY r.riskLevel")
    List<Object[]> countLandslidesByRiskLevel();

    @Query("SELECT COUNT(l) FROM LandslideEvent l WHERE l.riskZone IS NULL")
    long countUnassignedLandslides();

    long countBySource(String source);

    List<LandslideEvent> findBySource(String source);

    List<LandslideEvent> findByDistrict(String district);

    List<LandslideEvent> findBySourceAndDistrict(String source, String district);

    @Query(value = """
            SELECT *
            FROM landslide_events le
            WHERE le.location && ST_MakeEnvelope(:minLon, :minLat, :maxLon, :maxLat, 4326)
            LIMIT :limit
            """, nativeQuery = true)
    List<LandslideEvent> findLandslidesInBoundingBox(
            @Param("minLon") Double minLon,
            @Param("minLat") Double minLat,
            @Param("maxLon") Double maxLon,
            @Param("maxLat") Double maxLat,
            @Param("limit") int limit
    );

    @Query("SELECT l.district, COUNT(l) FROM LandslideEvent l WHERE l.source = :source AND l.district IS NOT NULL GROUP BY l.district ORDER BY COUNT(l) DESC")
    List<Object[]> countLandslidesByDistrict(@Param("source") String source);
}


