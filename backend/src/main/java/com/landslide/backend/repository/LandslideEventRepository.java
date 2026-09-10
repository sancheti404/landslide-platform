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
}

